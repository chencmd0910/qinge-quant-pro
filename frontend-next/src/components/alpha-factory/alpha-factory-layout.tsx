import ActiveColumn from "./active-column";
import WatchlistColumn from "./watchlist-column";
import RetiredColumn from "./retired-column";
import FactoryHeader from "./factory-header";

export default function AlphaFactoryLayout() {
  return (
    <div className="h-full flex flex-col gap-4">
      <FactoryHeader />
      <div className="flex-1 grid grid-cols-12 gap-4 min-h-0">
        {/* ACTIVE */}
        <div className="col-span-4">
          <ActiveColumn />
        </div>

        {/* WATCHLIST */}
        <div className="col-span-4">
          <WatchlistColumn />
        </div>

        {/* RETIRED */}
        <div className="col-span-4">
          <RetiredColumn />
        </div>
      </div>
    </div>
  );
}
