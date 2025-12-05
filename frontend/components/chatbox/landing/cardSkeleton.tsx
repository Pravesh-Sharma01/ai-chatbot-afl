const CardSkeleton = () => {
  return (
    <div className="flex flex-col gap-4 p-4 bg-white shadow-md animate-pulse items-start justify-center rounded-xl border border-solid border-stone-300 px-5 py-4 text-center min-w-2xs">
      <div className="h-4 bg-gray-200 rounded w-full"></div>
      <div className="h-4 bg-gray-200 rounded w-full"></div>
    </div>
  );
};

export default CardSkeleton;
