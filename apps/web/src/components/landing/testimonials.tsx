import { Quote } from "lucide-react";

const SECTION_TITLE = "{TESTIMONIAL_SECTION_TITLE}";
const SECTION_SUBTITLE = "{TESTIMONIAL_SECTION_SUBTITLE}";

const TESTIMONIALS = [
  { quote: "{TESTIMONIAL_1_QUOTE}", author: "{TESTIMONIAL_1_AUTHOR}", role: "{TESTIMONIAL_1_ROLE}" },
  { quote: "{TESTIMONIAL_2_QUOTE}", author: "{TESTIMONIAL_2_AUTHOR}", role: "{TESTIMONIAL_2_ROLE}" },
  { quote: "{TESTIMONIAL_3_QUOTE}", author: "{TESTIMONIAL_3_AUTHOR}", role: "{TESTIMONIAL_3_ROLE}" },
];

export function LandingTestimonials() {
  return (
    <section className="py-20 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-3 tracking-tight">{SECTION_TITLE}</h2>
          <p className="text-muted-foreground max-w-xl mx-auto">{SECTION_SUBTITLE}</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {TESTIMONIALS.map((t, i) => (
            <figure
              key={i}
              className="bg-card border rounded-xl p-6 flex flex-col gap-4 hover:shadow-md transition-shadow"
            >
              <Quote className="h-6 w-6 text-gold" />
              <blockquote className="text-sm text-foreground leading-relaxed">
                &ldquo;{t.quote}&rdquo;
              </blockquote>
              <figcaption className="mt-auto">
                <p className="font-semibold text-sm">{t.author}</p>
                <p className="text-xs text-muted-foreground">{t.role}</p>
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}
