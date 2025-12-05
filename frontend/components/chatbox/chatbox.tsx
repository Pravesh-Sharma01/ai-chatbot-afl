// src/components/chatbox/chatbox.tsx

"use client";

import TextInput from "./textInput";
import Conversation from "./conversation/conversation";
import ReactQueryClientProvider from "@/providers/ReactQueryClientProvider";
import Landing from "./landing/landing";
import { useAtom } from "jotai";
import { messageAtom } from "@/lib/state";
import LandingWithCards from "./landing/landingWithCards";

// Update the ChatBoxProps interface to include the new prop
export type ChatBoxProps = {
  withCards: boolean;
  withAttachButton?: boolean; // Add this prop
};

const ChatBox = (props: ChatBoxProps) => {
  const [msgs] = useAtom(messageAtom);

  return (
    <ReactQueryClientProvider>
      <div className="h-auto w-full mt-auto">
        <div className="flex w-full flex-col px-5 pb-20 text-neutral-700 max-md:mt-10 max-md:max-w-full text-center ">
          {msgs?.length === 0 ? (
            props.withCards ? (
              <LandingWithCards />
            ) : (
              <Landing />
            )
          ) : (
            <Conversation />
          )}
          {/* Pass the new prop down to the TextInput component */}
          <TextInput withAttachButton={props.withAttachButton} />
        </div>
      </div>
    </ReactQueryClientProvider>
  );
};

export default ChatBox;