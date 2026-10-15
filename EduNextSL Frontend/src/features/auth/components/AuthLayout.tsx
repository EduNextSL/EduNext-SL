import { useEffect, useState, type ReactNode } from "react";
import pastQuestionsIllustration from "../../../assets/Login Past Questions Illustration.png";
import internshipsIllustration from "../../../assets/Login Internships Illustration.png";
import scholarshipIllustration from "../../../assets/Login Scholarship Illustration.png";
import eduNextLogo from "../../../assets/logo.jpg";
import { useTranslation } from "react-i18next";

const promoSlides = [
  {
    key: "pastQuestions",
    image: pastQuestionsIllustration,
  },
  {
    key: "internships",
    image: internshipsIllustration,
  },
  {
    key: "scholarships",
    image: scholarshipIllustration,
  },
] as const;

type AuthLayoutProps = {
  variant?: "login" | "register";
  title: string;
  subtitle: string;
  form: ReactNode;
};

export function AuthLayout({
  variant = "login",
  title,
  subtitle,
  form,
}: AuthLayoutProps) {
  const [activeSlide, setActiveSlide] = useState(0);
  const { t, i18n } = useTranslation();

  useEffect(() => {
    const timer = window.setInterval(() => {
      setActiveSlide((current) => (current + 1) % promoSlides.length);
    }, 4000);

    return () => window.clearInterval(timer);
  }, []);

  const activePromo = promoSlides[activeSlide];
  const activePromoKey = `promo.${activePromo.key}`;

  return (
    <div className={`auth-shell auth-shell--${variant}`}>
      <label className="language-control">
        <span>{t("language.label")}</span>
        <select
          value={i18n.resolvedLanguage ?? i18n.language}
          onChange={(event) => {
            const nextLanguage = event.currentTarget.value;
            window.localStorage.setItem("edunextsl-language", nextLanguage);
            void i18n.changeLanguage(nextLanguage);
          }}
        >
          <option value="en">English</option>
          <option value="kri">Krio</option>
          <option value="fr">Français</option>
        </select>
      </label>

      <section className="auth-panel auth-panel--form">
        <div className="auth-brand" aria-label={t("accessibility.logo")}>
          <img src={eduNextLogo} alt={t("accessibility.logoAlt")} />
        </div>

        <div className="auth-form-shell">
          <h1>{title}</h1>
          <p className="auth-subtitle">{subtitle}</p>
          {form}
        </div>
      </section>

      <aside className="auth-panel auth-panel--promo">
        <div className="promo-pattern" aria-hidden="true" />
        <div className="promo-body">
          <p className="promo-tag">{t(`${activePromoKey}.tag`)}</p>
          <div className="promo-carousel">
            <div
              className="promo-carousel-track"
              style={{ transform: `translateX(-${activeSlide * 100}%)` }}
            >
              {promoSlides.map((slide) => (
                <div className="promo-slide" key={slide.key}>
                  <div className="promo-illustration-wrap">
                    <img
                      className="promo-illustration"
                      src={slide.image}
                      alt={t(`promo.${slide.key}.alt`)}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <h2>{t(`${activePromoKey}.title`)}</h2>
          <p className="promo-copy">{t(`${activePromoKey}.description`)}</p>

          <div
            className="promo-dots"
            aria-label={t("accessibility.slideIndicators")}
          >
            {promoSlides.map((slide, index) => (
              <button
                key={slide.key}
                type="button"
                className={
                  index === activeSlide ? "promo-dot active" : "promo-dot"
                }
                onClick={() => setActiveSlide(index)}
                aria-label={t("accessibility.viewSlide", {
                  title: t(`promo.${slide.key}.title`),
                })}
              />
            ))}
          </div>
        </div>
      </aside>
    </div>
  );
}
