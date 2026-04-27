/// <reference types="react" />

/**
 * Type shims for Shadcn UI components.
 *
 * The Shadcn primitives currently live in `.jsx` files without explicit
 * prop types. To keep migration velocity high and let `.tsx` consumers
 * compile cleanly, we widen every export to a permissive function type
 * that accepts:
 *   - any props (including `children`, `className`, `onClick`, `ref`,
 *     `data-*`, `aria-*`, etc.)
 *   - returns any React node
 *
 * Trade-off: prop typos on these specific components are NOT caught at
 * compile time. A future PR can replace each entry with an accurate
 * signature once the .jsx primitives are migrated to .tsx with proper
 * exports.
 *
 * IMPORTANT: This file MUST stay ambient (no top-level `import` / `export`).
 * Adding a top-level import would turn it into a module and the
 * `declare module` blocks below would no longer register globally.
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyShadcn = (props: any) => import("react").ReactElement | null;
type AnyVariants = (...args: unknown[]) => string;

declare module "@/components/ui/button" {
  export const Button: AnyShadcn;
  export const buttonVariants: AnyVariants;
}

declare module "@/components/ui/input" {
  export const Input: AnyShadcn;
}

declare module "@/components/ui/textarea" {
  export const Textarea: AnyShadcn;
}

declare module "@/components/ui/badge" {
  export const Badge: AnyShadcn;
  export const badgeVariants: AnyVariants;
}

declare module "@/components/ui/switch" {
  export const Switch: AnyShadcn;
}

declare module "@/components/ui/label" {
  export const Label: AnyShadcn;
}

declare module "@/components/ui/separator" {
  export const Separator: AnyShadcn;
}

declare module "@/components/ui/tabs" {
  export const Tabs: AnyShadcn;
  export const TabsList: AnyShadcn;
  export const TabsTrigger: AnyShadcn;
  export const TabsContent: AnyShadcn;
}

declare module "@/components/ui/dialog" {
  export const Dialog: AnyShadcn;
  export const DialogTrigger: AnyShadcn;
  export const DialogContent: AnyShadcn;
  export const DialogHeader: AnyShadcn;
  export const DialogFooter: AnyShadcn;
  export const DialogTitle: AnyShadcn;
  export const DialogDescription: AnyShadcn;
  export const DialogClose: AnyShadcn;
}

declare module "@/components/ui/alert-dialog" {
  export const AlertDialog: AnyShadcn;
  export const AlertDialogTrigger: AnyShadcn;
  export const AlertDialogContent: AnyShadcn;
  export const AlertDialogHeader: AnyShadcn;
  export const AlertDialogFooter: AnyShadcn;
  export const AlertDialogTitle: AnyShadcn;
  export const AlertDialogDescription: AnyShadcn;
  export const AlertDialogAction: AnyShadcn;
  export const AlertDialogCancel: AnyShadcn;
  export const AlertDialogPortal: AnyShadcn;
  export const AlertDialogOverlay: AnyShadcn;
}

declare module "@/components/ui/card" {
  export const Card: AnyShadcn;
  export const CardHeader: AnyShadcn;
  export const CardFooter: AnyShadcn;
  export const CardTitle: AnyShadcn;
  export const CardDescription: AnyShadcn;
  export const CardContent: AnyShadcn;
}

declare module "@/components/ui/select" {
  export const Select: AnyShadcn;
  export const SelectGroup: AnyShadcn;
  export const SelectValue: AnyShadcn;
  export const SelectTrigger: AnyShadcn;
  export const SelectContent: AnyShadcn;
  export const SelectLabel: AnyShadcn;
  export const SelectItem: AnyShadcn;
  export const SelectSeparator: AnyShadcn;
}

declare module "@/components/ui/sonner" {
  export const Toaster: AnyShadcn;
}

declare module "@/components/ui/popover" {
  export const Popover: AnyShadcn;
  export const PopoverTrigger: AnyShadcn;
  export const PopoverContent: AnyShadcn;
}

declare module "@/components/ui/tooltip" {
  export const Tooltip: AnyShadcn;
  export const TooltipTrigger: AnyShadcn;
  export const TooltipContent: AnyShadcn;
  export const TooltipProvider: AnyShadcn;
}

declare module "@/components/ui/scroll-area" {
  export const ScrollArea: AnyShadcn;
  export const ScrollBar: AnyShadcn;
}

declare module "@/components/ui/accordion" {
  export const Accordion: AnyShadcn;
  export const AccordionItem: AnyShadcn;
  export const AccordionTrigger: AnyShadcn;
  export const AccordionContent: AnyShadcn;
}

declare module "@/components/ui/avatar" {
  export const Avatar: AnyShadcn;
  export const AvatarImage: AnyShadcn;
  export const AvatarFallback: AnyShadcn;
}

declare module "@/components/ui/progress" {
  export const Progress: AnyShadcn;
}

declare module "@/components/ui/checkbox" {
  export const Checkbox: AnyShadcn;
}

declare module "@/components/ui/alert" {
  export const Alert: AnyShadcn;
  export const AlertTitle: AnyShadcn;
  export const AlertDescription: AnyShadcn;
}

declare module "@/components/ui/skeleton" {
  export const Skeleton: AnyShadcn;
}

declare module "@/components/ui/table" {
  export const Table: AnyShadcn;
  export const TableHeader: AnyShadcn;
  export const TableBody: AnyShadcn;
  export const TableFooter: AnyShadcn;
  export const TableHead: AnyShadcn;
  export const TableRow: AnyShadcn;
  export const TableCell: AnyShadcn;
  export const TableCaption: AnyShadcn;
}

declare module "@/components/ui/dropdown-menu" {
  export const DropdownMenu: AnyShadcn;
  export const DropdownMenuTrigger: AnyShadcn;
  export const DropdownMenuContent: AnyShadcn;
  export const DropdownMenuItem: AnyShadcn;
  export const DropdownMenuLabel: AnyShadcn;
  export const DropdownMenuSeparator: AnyShadcn;
  export const DropdownMenuCheckboxItem: AnyShadcn;
  export const DropdownMenuGroup: AnyShadcn;
  export const DropdownMenuPortal: AnyShadcn;
  export const DropdownMenuRadioGroup: AnyShadcn;
  export const DropdownMenuRadioItem: AnyShadcn;
  export const DropdownMenuShortcut: AnyShadcn;
  export const DropdownMenuSub: AnyShadcn;
  export const DropdownMenuSubContent: AnyShadcn;
  export const DropdownMenuSubTrigger: AnyShadcn;
}

declare module "@/components/ui/slider" {
  export const Slider: AnyShadcn;
}

declare module "@/components/ui/sheet" {
  export const Sheet: AnyShadcn;
  export const SheetTrigger: AnyShadcn;
  export const SheetClose: AnyShadcn;
  export const SheetContent: AnyShadcn;
  export const SheetHeader: AnyShadcn;
  export const SheetFooter: AnyShadcn;
  export const SheetTitle: AnyShadcn;
  export const SheetDescription: AnyShadcn;
  export const SheetPortal: AnyShadcn;
  export const SheetOverlay: AnyShadcn;
}

declare module "@/components/ui/carousel" {
  export const Carousel: AnyShadcn;
  export const CarouselContent: AnyShadcn;
  export const CarouselItem: AnyShadcn;
  export const CarouselPrevious: AnyShadcn;
  export const CarouselNext: AnyShadcn;
  export type CarouselApi = unknown;
}

declare module "@/components/ui/form" {
  export const Form: AnyShadcn;
  export const FormItem: AnyShadcn;
  export const FormLabel: AnyShadcn;
  export const FormControl: AnyShadcn;
  export const FormDescription: AnyShadcn;
  export const FormMessage: AnyShadcn;
  export const FormField: AnyShadcn;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  export const useFormField: () => any;
}

// Catch-all for any Shadcn component we haven't declared yet.
declare module "@/components/ui/*" {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const Anything: any;
  export default Anything;
  export = Anything;
}
