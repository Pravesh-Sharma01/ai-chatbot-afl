import ChatBox from "@/components/chatbox/chatbox";

export default function fiber() {
  return (
    <div className="flex-1 flex">
      <ChatBox withCards={false} withAttachButton={false} />
    </div>
  );
}
