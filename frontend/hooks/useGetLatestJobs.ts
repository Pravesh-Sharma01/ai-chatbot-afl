import { LatestJobs } from "@/lib/types";
import { useMutation } from "@tanstack/react-query";


export const useGetLatestJobs = () => {
  return useMutation<LatestJobs, Error, void>({
    mutationKey: ["latestJobs"],

    mutationFn: async () => {
      try {
        const response = await fetch("/api/jobs/latest");

        if (!response.ok) {
          // Try to parse JSON error first
          let errorMessage = "Failed to fetch latest jobs";

          try {
            const errorJson = await response.json();
            errorMessage = errorJson.message || JSON.stringify(errorJson);
          } catch {
            // If not JSON, fallback to text
            errorMessage = await response.text();
          }

          throw new Error(errorMessage);
        }

        // This already returns parsed JSON
        const jobs: LatestJobs = await response.json();
        return jobs;
      } catch (error) {
        console.error("Get Latest Jobs Hook:", error);
        throw error;
      }
    }
  });
};
