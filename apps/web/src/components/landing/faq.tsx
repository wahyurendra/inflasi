import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const SECTION_TITLE = "{FAQ_SECTION_TITLE}";
const SECTION_SUBTITLE = "{FAQ_SECTION_SUBTITLE}";

const FAQS = [
  { q: "{FAQ_1_Q}", a: "{FAQ_1_A}" },
  { q: "{FAQ_2_Q}", a: "{FAQ_2_A}" },
  { q: "{FAQ_3_Q}", a: "{FAQ_3_A}" },
  { q: "{FAQ_4_Q}", a: "{FAQ_4_A}" },
  { q: "{FAQ_5_Q}", a: "{FAQ_5_A}" },
  { q: "{FAQ_6_Q}", a: "{FAQ_6_A}" },
];

export function LandingFaq() {
  return (
    <section id="faq" className="py-20 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold mb-3 tracking-tight">{SECTION_TITLE}</h2>
          <p className="text-muted-foreground">{SECTION_SUBTITLE}</p>
        </div>
        <Accordion type="single" collapsible className="w-full">
          {FAQS.map((f, i) => (
            <AccordionItem key={i} value={`q-${i}`}>
              <AccordionTrigger className="text-left">{f.q}</AccordionTrigger>
              <AccordionContent>{f.a}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  );
}
