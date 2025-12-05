import { useMutation, UseMutationResult } from "@tanstack/react-query";
import { usePathname } from "next/navigation";

export type SendQueryResponse = {
  reply: string;
};

export const useSendQuery = (): UseMutationResult<
  SendQueryResponse,
  Error,
  string
> => {
  const pathname = usePathname();
  return useMutation<SendQueryResponse, Error, string>({
    mutationKey: ["query"],
    mutationFn: async (query: string) => {
      let apiEndpoint = "";
      if (pathname.includes("sales/motor")) {
        apiEndpoint = "/api/sales/motor/chat";
      } else if (pathname.includes("sales/fiber")) {
        apiEndpoint = "/api/sales/fiber/chat";
      } else if (pathname.includes("hr")) {
        apiEndpoint = "/api/hr/chat";
      } else if (pathname.includes("claim")) {
        apiEndpoint = "/api/claim/chat";
      }

      const payload = {
        message: query,
        session_id: sessionStorage.getItem("chatSessionId"),
      };

      try {
        const response = await fetch(apiEndpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          const errorMessage = await response.text();
          throw new Error(errorMessage);
        }

        const responseJSON: SendQueryResponse = await response.json();
        return responseJSON;
      } catch (error) {
        console.error("Send Query Hook:", error);
        throw error;
      }
    },
  });
};
