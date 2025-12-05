import { atom } from "jotai";
import { Jobs, Message } from "./types";


export const messageAtom = atom<Array<Message>>([]);

export const botThinkingAtom = atom<boolean>(false);

export const selectedCardJobAtom = atom<Jobs | null>(null);
