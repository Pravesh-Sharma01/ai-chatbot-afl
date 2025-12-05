// src/app/motor/page.tsx or similar view file

import ChatBox from "@/components/chatbox/chatbox";

export default function motor() {
  return (
    <div className="flex-1 flex">
      <ChatBox withCards={false} withAttachButton={false} />
    </div>
  );
}