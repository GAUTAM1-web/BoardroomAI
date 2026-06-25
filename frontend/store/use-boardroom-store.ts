import { create } from "zustand";

import type { BoardMeetingResult } from "@/lib/types";

type BoardroomState = {
  latestResult: BoardMeetingResult | null;
  setLatestResult: (result: BoardMeetingResult) => void;
  clearLatestResult: () => void;
};

export const useBoardroomStore = create<BoardroomState>((set) => ({
  latestResult: null,
  setLatestResult: (result) => set({ latestResult: result }),
  clearLatestResult: () => set({ latestResult: null })
}));

