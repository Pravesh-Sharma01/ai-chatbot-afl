import { LatestJobs } from "@/lib/types";
import { useMutation } from "@tanstack/react-query";


export const useGetLatestJobs = () => {
  return useMutation<LatestJobs, Error, void>({
    mutationKey: ["latestJobs"],
    mutationFn: async () => {
      try {
        const response = await fetch("/api/jobs/latest", {
          method: "GET",
        });

        if (!response.ok) {
          const errorMessage = await response.text();
          console.error("Error fetching latest jobs:", errorMessage);
          throw new Error(errorMessage);
        }

        const responseJSON: string = (await response.json());
        const jobs = await JSON.parse(responseJSON);
        return jobs as LatestJobs;
      } catch (error) {
        console.error("Get Latest Jobs Hook:", error);
        throw error;
      }
    },
  });
};
