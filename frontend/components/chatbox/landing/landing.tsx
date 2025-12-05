'use client";';

import { useEffect } from "react";
import Image from "next/image";

const Landing = () => {
  useEffect(() => {
    (async () => {
      try {
        let sessionId = sessionStorage.getItem("chatSessionId");
        if (!sessionId) {
          sessionId = Date.now().toString();
          sessionStorage.setItem("chatSessionId", sessionId);
        }
      } catch (error) {
        console.error("Error in sending query: ", error);
      }
    })();
  }, []);

  return (
    <div className="mb-60">
      <div>
        <div className="text-4xl leading-[64px] tracking-tight max-md:max-w-full">
          Interact with
        </div>
        <div className="mt-2 mx-auto flex flex-wrap items-start md:items-center justify-center gap-5 self-start whitespace-nowrap text-7xl font-bold tracking-tight max-md:flex-wrap max-md:text-4xl">
          <div className="md:mt-2.5">
            <Image
              src={"/logo.svg"}
              width={90}
              height={70}
              alt={"Formica Logo"}
            />
          </div>
          <div className="max-md:text-4xl">AI</div>
          <div className="max-md:text-4xl">Engage</div>
        </div>
      </div>
    </div>
  );
};

export default Landing;
