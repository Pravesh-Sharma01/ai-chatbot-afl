'use client";'

import { useEffect, useState } from "react";
import CardSkeleton from "./cardSkeleton";
import Hero from "./hero";
import { Jobs } from "@/lib/types";
import { useGetLatestJobs } from "@/hooks/useGetLatestJobs";
import Card from "./card";

const LandingWithCards = () => {
  const { mutateAsync: getLatestJobs } = useGetLatestJobs();
  const [jobs, setJobs] = useState<Array<Jobs>>([]);

  useEffect(() => {
    (async () => {
      try {
        let sessionId = sessionStorage.getItem("chatSessionId");
        if (!sessionId) {
          sessionId = Date.now().toString();
          sessionStorage.setItem("chatSessionId", sessionId);
        }
        const response = await getLatestJobs();
        setJobs(response.jobs);
      } catch (error) {
        console.error("Error in sending query: ", error);
      }
    })();
  }, []);

  return (
    <div>
      <Hero />
      <div className="m-auto mt-5 flex gap-5 max-md:mt-10 max-md:max-w-full flex-wrap max-md:pr-5 min-w-40 md:justify-center md:max-w-[980px]">
        {jobs?.length === 0 ? (
          <>
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </>
        ) : (
          <>
            {jobs?.slice(0, 6).map((job) => (
              <Card key={job.id} job={job} />
            ))}
          </>
        )}
      </div>
    </div>
  );
};

export default LandingWithCards;
