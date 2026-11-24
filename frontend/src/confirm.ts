import { createContext, useContext } from 'react'

export type ConfirmOptions = {
  title?: string
  confirmLabel?: string
  danger?: boolean
}

export type ConfirmFn = (message: string, options?: ConfirmOptions) => Promise<boolean>

export const ConfirmContext = createContext<ConfirmFn>(() => Promise.resolve(false))

export function useConfirm(): ConfirmFn {
  return useContext(ConfirmContext)
}
