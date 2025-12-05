import { useAtom } from "jotai";
import { MouseEvent } from "react";
import { selectedCardJobAtom } from "@/lib/state";
import { Jobs } from "@/lib/types";

type CardProps = {
  job: Jobs;
};

const Card = (props: CardProps) => {
  const [selectedCardJob, setCardJob] = useAtom(selectedCardJobAtom);

  const boldContent = `${props.job.job_title}`;
  const normalContent = `(${props.job.min_experience} ${
    props.job.min_experience > 1 ? "years" : "year"
  }) ${
    typeof props.job.location === "string"
      ? props.job.location
      : props.job.location?.[0]
  }`;

  const handleClick = (ev: MouseEvent<HTMLDivElement>) => {
    ev.stopPropagation();
    ev.preventDefault();
    if (selectedCardJob === null) setCardJob(props.job);
  };

  return (
    <div
      className="flex flex-col items-start justify-center rounded-xl border border-solid border-stone-300 px-5 py-4 text-center cursor-pointer transform transition-transform duration-300 hover:scale-105"
      onClick={handleClick}
    >
      <div className="text-sm font-semibold leading-4 w-full">
        {boldContent}
      </div>
      <div className="mt-1.5 text-xs leading-4 w-full">{normalContent}</div>
    </div>
  );
};

export default Card;
