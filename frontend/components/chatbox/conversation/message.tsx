import Image from "next/image";
import { MouseEvent } from "react";
import markdownit from "markdown-it";
import toast, { Toaster } from "react-hot-toast";
import { Message as MessageType, SENDER } from "@/lib/types";
import { getFormattedTimestamp } from "@/lib/utils/timestampFormatter";
import "./conversation.css";

type MessagePropType = {
  message: MessageType;
};

const Message = (props: MessagePropType) => {
  const md = markdownit();

  const copyToClipboad = (ev: MouseEvent<HTMLButtonElement>) => {
    const target = ev.target as HTMLElement;
    if (target.parentElement?.nextSibling?.textContent) {
      navigator.clipboard.writeText(
        target.parentElement?.nextSibling?.textContent
      );
      // Notification for successful copy message
      toast.success("Copied to Clipboard", {
        style: {
          marginTop: "80px",
        },
      });
    }
  };

  return (
    <>
      <Toaster />
      {props.message.sender === SENDER.USER ? (
        <div className="flex w-full flex-col items-end mt-5">
          <span className="mb-2 mt-2 min-w-1/3 max-w-5/6 sm:max-w-2/3 rounded-lg px-2 py-4 text-left border border-gray-200 shadow-lg relative">
            <div className="absolute -top-7">
              <Image
                aria-hidden
                src="/user_avatar.png"
                alt="copy"
                width={14}
                height={14}
                className="inline-block mr-1"
              />
              You
            </div>
            <div>{props.message.content}</div>
            {props.message.attachment && (
              <div className="text-xs pt-1 pb-2">
                <b>Attachment: </b>
                {props.message.attachment}
              </div>
            )}
            <p className="text-xs text-gray-500">
              Asked at {getFormattedTimestamp(props.message.timestamp)}
            </p>
          </span>
        </div>
      ) : (
        <div className="bot flex w-full flex-col flex-wrap items-start justify-center">
          <div>
            <Image
              aria-hidden
              src="/ai_avatar.png"
              alt="copy"
              width={14}
              height={16}
              className="inline-block mr-1"
            />
            AI Engage
          </div>
          <span className="relative mb-2 mt-2 min-w-2/3 max-w-5/6 sm:max-w-2/3 rounded-md border text-left border-solid border-[#c09b24] bg-white px-2 py-4 shadow-lg overflow-x-auto overflow-y-visible">
            <button
              className="absolute right-0 top-0 m-1 cursor-pointer"
              onClick={copyToClipboad}
            >
              <Image
                aria-hidden
                src="/_copy.png"
                alt="copy"
                width={12}
                height={12}
              />
            </button>
            <div
              dangerouslySetInnerHTML={{
                __html: md.render(props.message.content),
              }}
            />
          </span>
        </div>
      )}
    </>
  );
};

export default Message;
