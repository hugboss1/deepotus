/**
 * Type shims for Shadcn UI components.
 *
 * The Shadcn primitives currently live in `.jsx` files without explicit
 * prop types — TypeScript infers them as `React.ForwardRefExoticComponent
 * <RefAttributes<any>>`, which is too narrow (it rejects `children`,
 * `className`, `onClick`, etc.).
 *
 * Until each component is migrated to `.tsx` with proper typings, this
 * shim widens the inferred props to `React.ComponentProps<"div"> & any`
 * so call-sites in `.tsx` files compile cleanly. This is intentionally
 * permissive — the trade-off is: we keep migration velocity high while
 * accepting that prop typos won't be caught at compile time on these
 * specific components. A future PR can replace each entry with an
 * accurate signature.
 */
declare module "@/components/ui/button" {
  import * as React from "react";
  // Shadcn Button supports `variant`, `size`, `asChild`, plus all `<button>` attrs.
  // Using `any` here is pragmatic — Button is internally already typed correctly
  // at runtime, we just lack the .d.ts.
  export const Button: React.ForwardRefExoticComponent<any>;
  export const buttonVariants: (...args: any[]) => string;
}

declare module "@/components/ui/input" {
  import * as React from "react";
  export const Input: React.ForwardRefExoticComponent<any>;
}

declare module "@/components/ui/textarea" {
  import * as React from "react";
  export const Textarea: React.ForwardRefExoticComponent<any>;
}

declare module "@/components/ui/badge" {
  import * as React from "react";
  export const Badge: React.FC<any>;
  export const badgeVariants: (...args: any[]) => string;
}

declare module "@/components/ui/switch" {
  import * as React from "react";
  export const Switch: React.ForwardRefExoticComponent<any>;
}

declare module "@/components/ui/label" {
  import * as React from "react";
  export const Label: React.ForwardRefExoticComponent<any>;
}

declare module "@/components/ui/separator" {
  import * as React from "react";
  export const Separator: React.ForwardRefExoticComponent<any>;
}

declare module "@/components/ui/tabs" {
  import * as React from "react";
  export const Tabs: React.FC<any>;
  export const TabsList: React.ForwardRefExoticComponent<any>;
  export const TabsTrigger: React.ForwardRefExoticComponent<any>;
  export const TabsContent: React.ForwardRefExoticComponent<any>;
}

declare module "@/components/ui/dialog" {
  import * as React from "react";
  export const Dialog: React.FC<any>;
  export const DialogTrigger: React.FC<any>;
  export const DialogContent: React.ForwardRefExoticComponent<any>;
  export const DialogHeader: React.FC<any>;
  export const DialogFooter: React.FC<any>;
  export const DialogTitle: React.ForwardRefExoticComponent<any>;
  export const DialogDescription: React.ForwardRefExoticComponent<any>;
  export const DialogClose: React.FC<any>;
}

declare module "@/components/ui/card" {
  import * as React from "react";
  export const Card: React.ForwardRefExoticComponent<any>;
  export const CardHeader: React.ForwardRefExoticComponent<any>;
  export const CardFooter: React.ForwardRefExoticComponent<any>;
  export const CardTitle: React.ForwardRefExoticComponent<any>;
  export const CardDescription: React.ForwardRefExoticComponent<any>;
  export const CardContent: React.ForwardRefExoticComponent<any>;
}

declare module "@/components/ui/select" {
  import * as React from "react";
  export const Select: React.FC<any>;
  export const SelectGroup: React.FC<any>;
  export const SelectValue: React.FC<any>;
  export const SelectTrigger: React.ForwardRefExoticComponent<any>;
  export const SelectContent: React.ForwardRefExoticComponent<any>;
  export const SelectLabel: React.ForwardRefExoticComponent<any>;
  export const SelectItem: React.ForwardRefExoticComponent<any>;
  export const SelectSeparator: React.ForwardRefExoticComponent<any>;
}

declare module "@/components/ui/sonner" {
  import * as React from "react";
  export const Toaster: React.FC<any>;
}

declare module "@/components/ui/popover" {
  import * as React from "react";
  export const Popover: React.FC<any>;
  export const PopoverTrigger: React.FC<any>;
  export const PopoverContent: React.ForwardRefExoticComponent<any>;
}

declare module "@/components/ui/tooltip" {
  import * as React from "react";
  export const Tooltip: React.FC<any>;
  export const TooltipTrigger: React.FC<any>;
  export const TooltipContent: React.ForwardRefExoticComponent<any>;
  export const TooltipProvider: React.FC<any>;
}

declare module "@/components/ui/scroll-area" {
  import * as React from "react";
  export const ScrollArea: React.ForwardRefExoticComponent<any>;
  export const ScrollBar: React.ForwardRefExoticComponent<any>;
}

declare module "@/components/ui/accordion" {
  import * as React from "react";
  export const Accordion: React.FC<any>;
  export const AccordionItem: React.ForwardRefExoticComponent<any>;
  export const AccordionTrigger: React.ForwardRefExoticComponent<any>;
  export const AccordionContent: React.ForwardRefExoticComponent<any>;
}

declare module "@/components/ui/avatar" {
  import * as React from "react";
  export const Avatar: React.ForwardRefExoticComponent<any>;
  export const AvatarImage: React.ForwardRefExoticComponent<any>;
  export const AvatarFallback: React.ForwardRefExoticComponent<any>;
}

declare module "@/components/ui/progress" {
  import * as React from "react";
  export const Progress: React.ForwardRefExoticComponent<any>;
}

declare module "@/components/ui/checkbox" {
  import * as React from "react";
  export const Checkbox: React.ForwardRefExoticComponent<any>;
}

declare module "@/components/ui/alert" {
  import * as React from "react";
  export const Alert: React.ForwardRefExoticComponent<any>;
  export const AlertTitle: React.ForwardRefExoticComponent<any>;
  export const AlertDescription: React.ForwardRefExoticComponent<any>;
}

declare module "@/components/ui/skeleton" {
  import * as React from "react";
  export const Skeleton: React.FC<any>;
}

declare module "@/components/ui/dropdown-menu" {
  import * as React from "react";
  export const DropdownMenu: React.FC<any>;
  export const DropdownMenuTrigger: React.FC<any>;
  export const DropdownMenuContent: React.ForwardRefExoticComponent<any>;
  export const DropdownMenuItem: React.ForwardRefExoticComponent<any>;
  export const DropdownMenuLabel: React.ForwardRefExoticComponent<any>;
  export const DropdownMenuSeparator: React.ForwardRefExoticComponent<any>;
  export const DropdownMenuCheckboxItem: React.ForwardRefExoticComponent<any>;
  export const DropdownMenuGroup: React.FC<any>;
  export const DropdownMenuPortal: React.FC<any>;
  export const DropdownMenuRadioGroup: React.FC<any>;
  export const DropdownMenuRadioItem: React.ForwardRefExoticComponent<any>;
  export const DropdownMenuShortcut: React.FC<any>;
  export const DropdownMenuSub: React.FC<any>;
  export const DropdownMenuSubContent: React.ForwardRefExoticComponent<any>;
  export const DropdownMenuSubTrigger: React.ForwardRefExoticComponent<any>;
}

// Catch-all for any Shadcn component we haven't declared yet.
// New `@/components/ui/<x>` imports will resolve to "any" exports.
declare module "@/components/ui/*" {
  const Anything: any;
  export default Anything;
  export = Anything;
}
