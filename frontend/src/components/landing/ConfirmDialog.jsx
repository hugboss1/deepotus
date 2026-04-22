import React from "react";
import { useI18n } from "@/i18n/I18nProvider";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

export default function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  onConfirm,
  destructive = false,
  testIdPrefix = "confirm",
}) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent data-testid={`${testIdPrefix}-dialog`}>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          {description && (
            <AlertDialogDescription>{description}</AlertDialogDescription>
          )}
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel data-testid={`${testIdPrefix}-cancel`}>
            {cancelLabel}
          </AlertDialogCancel>
          <AlertDialogAction
            data-testid={`${testIdPrefix}-action`}
            onClick={() => onConfirm?.()}
            className={destructive ? "bg-destructive hover:bg-destructive/90 text-destructive-foreground" : ""}
          >
            {confirmLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

// Re-export translation-friendly wrapper (unused for now)
export function useConfirm() {
  const { t } = useI18n();
  return { t };
}
