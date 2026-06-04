import { create } from 'zustand'
import type { FilterState, Platform } from '@/types'

interface FilterStore extends FilterState {
  setPlatform: (v: Platform | '') => void
  setSearch: (v: string) => void
  setFollowersRange: (min: number | '', max: number | '') => void
  setErRange: (min: number | '', max: number | '') => void
  setSortBy: (v: string) => void
  toggleOrder: () => void
  setNiche: (v: string) => void
  setPage: (n: number) => void
  reset: () => void
}

const defaults: FilterState = {
  platform: '',
  minFollowers: '',
  maxFollowers: '',
  minEr: '',
  maxEr: '',
  sortBy: 'followers',
  order: 'desc',
  search: '',
  niche: '',
  page: 1,
}

export const useFilterStore = create<FilterStore>((set) => ({
  ...defaults,

  setPlatform: (v) => set({ platform: v, page: 1 }),
  setSearch: (v) => set({ search: v, page: 1 }),
  setFollowersRange: (min, max) => set({ minFollowers: min, maxFollowers: max, page: 1 }),
  setErRange: (min, max) => set({ minEr: min, maxEr: max, page: 1 }),
  setSortBy: (v) => set({ sortBy: v, page: 1 }),
  toggleOrder: () => set((s) => ({ order: s.order === 'desc' ? 'asc' : 'desc', page: 1 })),
  setNiche: (v) => set({ niche: v, page: 1 }),
  setPage: (n) => set({ page: n }),
  reset: () => set(defaults),
}))
