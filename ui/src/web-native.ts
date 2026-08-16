import { AuditController } from "./web-native/audit"
import type { NativePageContext, NativePageController } from "./web-native/common"
import { FilesController } from "./web-native/files"
import { RemotesController } from "./web-native/remotes"
import { TerminalsController } from "./web-native/terminals"

export type { NativePageContext, NativePageController, NoticeTone } from "./web-native/common"

export type NativeViewName = "files" | "terminals" | "remotes" | "audit"

export function createNativePage(view: NativeViewName, context: NativePageContext): NativePageController {
  if (view === "files") return new FilesController(context)
  if (view === "terminals") return new TerminalsController(context)
  if (view === "remotes") return new RemotesController(context)
  return new AuditController(context)
}

export function isNativeView(view: string): view is NativeViewName {
  return ["files", "terminals", "remotes", "audit"].includes(view)
}
