import { create } from 'zustand'

type ActiveView = 'influencers' | 'brands'

interface ViewStore {
  activeView: ActiveView
  setActiveView: (v: ActiveView) => void
}

export const useViewStore = create<ViewStore>((set) => ({
  activeView: 'influencers',
  setActiveView: (v) => set({ activeView: v }),
}))
