import { useEffect } from "react";
import { useAtom } from "jotai";
import Message from "./message";
import { getFormattedTimestamp } from "@/lib/utils/timestampFormatter";
import { messageAtom } from "@/lib/state";

const Conversation = () => {
  const [msgs] = useAtom(messageAtom);

  useEffect(() => {
    msgs.sort((a, b) => {
      return a.timestamp.getTime() - b.timestamp.getTime();
    });
  }, [msgs]);

  return (
    <>
      {msgs.map((msg) => (
        <div key={getFormattedTimestamp(msg.timestamp)}>
          <Message message={msg} />
        </div>
      ))}
    </>
  );
};

export default Conversation;
