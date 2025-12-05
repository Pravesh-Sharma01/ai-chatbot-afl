// src/components/chatbox/textInput.tsx

"use client";

import { KeyboardEvent, useEffect, useRef, useState } from "react";
import Image from "next/image";
import { useAtom } from "jotai";
import toast, { Toaster } from "react-hot-toast";
import { Message, SENDER } from "@/lib/types";
import { useSendQuery } from "@/hooks/useSendQuery";
import { botThinkingAtom, messageAtom, selectedCardJobAtom } from "@/lib/state";
import Loader from "./loader";

// Add a new prop to the component
type TextInputProps = {
  withAttachButton?: boolean;
};

const TextInput = (props: TextInputProps) => {
  const [isBotThinking, setIsBotThinking] = useAtom(botThinkingAtom);
  const [msgs, setMsgs] = useAtom(messageAtom);
  const [selectedCardJob] = useAtom(selectedCardJobAtom);
  const inputRef = useRef<HTMLInputElement>(null);
  const attachmentRef = useRef<HTMLInputElement>(null);
  const { mutateAsync: sendQueryAPI } = useSendQuery();
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  useEffect(() => {
    scrollToBottom();
  }, [msgs]);

  useEffect(() => {
    if (selectedCardJob) {
      const message: Message = {
        sender: SENDER.USER,
        content: ` I want to apply for ${
          selectedCardJob.job_title
        } and I have ${selectedCardJob.min_experience} ${
          selectedCardJob.min_experience > 1 ? "years" : "year"
        }
          of experience`,
        timestamp: new Date(),
      };
      if (inputRef.current) inputRef.current.value = "";
      sendQuery(message.content);
    }
  }, [selectedCardJob]);

  const handleKeyUp = (ev: KeyboardEvent<HTMLInputElement>) => {
    if (ev.key.toLowerCase() !== "enter") return;
    sendQuery(inputRef.current?.value ?? "");
  };

  const handleClick = () => {
    sendQuery(inputRef.current?.value ?? "");
  };

  const sendQuery = async (query: string) => {
    if (!query) return;
    setIsBotThinking(true);
    const message: Message = {
      sender: SENDER.USER,
      content: query,
      attachment: fileName || undefined,
      timestamp: new Date(),
    };
    setMsgs((prev) => [...prev, message]);
    if (inputRef.current) inputRef.current.value = "";
    try {
      const response = await sendQueryAPI(
        fileContent
          ? message.content +
              "\n" +
              "Consider my job title, location and experiece from cv to search job" +
              "\n" +
              fileContent
          : message.content
      );
      const botMessage: Message = {
        sender: SENDER.BOT,
        content: response.reply,
        timestamp: new Date(),
      };
      setMsgs((prev) => [...prev, botMessage]);
      setIsBotThinking(false);
      setFileContent(null);
      setFileName(null);
    } catch (error) {
      setIsBotThinking(false);
      setFileContent(null);
      setFileName(null);
      console.error("Error in sending query: ", error);
    }
  };

  const scrollToBottom = () => {
    window.scrollTo({
      top: document.body.scrollHeight,
      behavior: "smooth",
    });
  };

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    try {
      if (file) {
        setFileName(file.name);

        if (file.type === "application/pdf") {
          if (typeof window !== "undefined") {
            const { default: pdfToText } = await import("react-pdftotext");
            const text = await pdfToText(file);
            setFileContent(text);
          }
        } else {
          const reader = new FileReader();
          reader.readAsText(file);
          reader.onload = (e) => {
            const result = e.target?.result;
            setFileContent(typeof result === "string" ? result : String(result));
          };
        }
      }
    } catch (error) {
      console.error("Error reading file: ", error);
      setFileContent(null);
      setFileName(null);
      if (attachmentRef.current) attachmentRef.current.value = "";
      toast.error("Failed to read file", {
        style: { marginTop: "80px" },
      });
    }
  };

  const removeFile = () => {
    setFileContent(null);
    setFileName(null);
    if (attachmentRef.current) attachmentRef.current.value = "";
  };

  return (
    <>
      <Toaster />
      {isBotThinking && <Loader />}
      <div className="bg-gredient-dark flex w-full max-w-full flex-col">
        <div className="search-box mx-auto my-auto flex w-full flex-wrap items-center justify-between sm:w-full md:w-full lg:w-full xl:w-full">
          <div className="mt-7 flex w-full rounded-lg border  border-gray-400 bg-gray-100 focus:border-gray-900 active:bg-white">
            {/* Conditional rendering of the attach button */}
            {props.withAttachButton !== false && (
              <div
                className="relative cursor-pointer px-3 pt-4 hover:bg-yellow-400 rounded-lg"
                onClick={() => attachmentRef.current?.click()}
              >
                <input
                  id="attachment"
                  className="hidden"
                  ref={attachmentRef}
                  type="file"
                  onChange={handleFileUpload}
                />
                <Image
                  src={"/attach-file.png"}
                  width={25}
                  height={30}
                  alt={"attach file"}
                />
                {fileName && (
                  <div className="inline-block group">
                    <span
                      className="absolute -top-1 -right-1 bg-yellow-400 text-white text-xs font-bold rounded-full w-4 h-4 hover:bg-red-600"
                      onClick={removeFile}
                    >
                      <span className="hidden group-hover:inline-block">X</span>
                    </span>
                  </div>
                )}
              </div>
            )}
            <div className="flex h-auto w-full">
              <input
                id="queryBox"
                ref={inputRef}
                className="text-grey-darker h-auto w-full rounded-lg border border-gray-100 bg-gray-100 active:bg-white p-4 text-lg font-medium text-gray-600 outline-none focus:border-transparent focus:ring-0 placeholder-gray-400"
                type="search"
                placeholder="Ask me anything..."
                onKeyUp={handleKeyUp}
                disabled={isBotThinking}
              />
              <button
                className="flex h-auto w-20 items-center justify-center rounded rounded-l-none bg-black cursor-pointer"
                onClick={handleClick}
              >
                <Image src={"/_send.png"} width={25} height={25} alt={"send"} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default TextInput;