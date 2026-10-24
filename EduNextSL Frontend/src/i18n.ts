import i18n from "i18next";
import { initReactI18next } from "react-i18next";

const resources = {
  en: {
    translation: {
      language: { label: "Language" },
      auth: {
        loading: "Loading...",
        connectionProblem: "We couldn't reach the server",
        tryAgain: "Try Again",
        continue: "Continue",
        showPassword: "Show password",
        hidePassword: "Hide password",
        signingIn: "Signing in...",
        creating: "Creating account...",
        enterEmailPassword: "Enter your email and password.",
        genericError: "Something went wrong. Please try again.",
        comingSoon: "Coming soon",
        googleUnavailable: "Google sign-in is not configured yet",
        googleLoadFailed: "Google sign-in could not be loaded. Check your connection.",
        googleTermsPrompt:
          "I agree to the Terms of Service, User Agreement and Privacy Policy, and want to create a student account with Google.",
        welcome: "Welcome, {{name}}",
        role: "Role",
        status: "Status",
        logout: "Log out",
        enterEmail: "Enter your email address.",
        forgotTitle: "Forgot your password?",
        forgotSubtitle: "Enter your email and we will send you a reset link.",
        sendLink: "Send reset link",
        sending: "Sending...",
        resetSent:
          "If an account exists for that email, a password reset link has been sent. Check your inbox.",
        backToLogin: "Back to login",
        resetTitle: "Choose a new password",
        resetSubtitle: "Your new password must be different from your old one.",
        newPassword: "New password",
        resetSubmit: "Reset password",
        saving: "Saving...",
        resetDone: "Your password has been reset. You can now log in.",
        resetLinkInvalid: "This reset link is invalid or has expired. Request a new one.",
      },
      common: {
        email: "Email",
        emailAddress: "Email address",
        password: "Password",
        confirmPassword: "Confirm password",
        companyName: "Company name",
        contactName: "Contact full name",
        workEmail: "Work email address",
        firstName: "First name",
        lastName: "Last name",
        passwordHelp: "Use at least 10 characters. Avoid common or all-number passwords.",
        termsPrefix: "I understand and agree to the",
        termsOfService: "Terms of Service",
        termsMiddle: ", User Agreement, and",
        privacyPolicy: "Privacy Policy",
        termsSuffix: ".",
        alreadyHaveAccount: "Already have an account?",
        signIn: "Sign in",
        googleSignup: "Sign up with Google",
        facebookSignup: "Sign up with Facebook",
      },
      login: {
        title: "Welcome Back",
        subtitle: "Please Login to your account",
        rememberMe: "Remember me",
        forgotPassword: "Forgot password?",
        submit: "LOGIN",
        divider: "Or",
        noAccount: "Don’t have an account?",
        signUp: "Sign up",
        google: "Continue with Google",
        facebook: "Continue with Facebook",
      },
      register: {
        studentTitle: "Create your account",
        companyTitle: "Register your company",
        studentSubtitle: "Your next opportunity starts here.",
        companySubtitle: "Connect your opportunities with student talent.",
        student: "Student",
        company: "Company",
        studentSubmit: "Create student account",
        companySubmit: "Create company account",
        divider: "Or sign up with",
      },
      accessibility: {
        logo: "EduNextSL logo",
        logoAlt: "EduNextSL Learning Solutions",
        slideIndicators: "Slide indicators",
        viewSlide: "View {{title}}",
      },
      promo: {
        pastQuestions: {
          tag: "ENDLESS PAST QUESTIONS",
          title: "Endless Past Questions",
          description:
            "Access verified past national exams and study guides to practise smarter, track your progress, and ace your exams",
          alt: "Illustration of students studying with past questions",
        },
        internships: {
          tag: "INTERNSHIPS",
          title: "Internships That Move You Forward",
          description:
            "Explore hands-on opportunities, build experience, and match with employers accelerating your next career move.",
          alt: "Illustration of an internship opportunity",
        },
        scholarships: {
          tag: "SCHOLARSHIPS",
          title: "Scholarships for the Next Step",
          description:
            "Discover funding opportunities and academic support programs designed to help students thrive and stay focused.",
          alt: "Illustration of a scholarship opportunity",
        },
      },
    },
  },
  kri: {
    translation: {
      language: { label: "Langwij" },
      common: {
        email: "I-mel",
        emailAddress: "I-mel adres",
        password: "Paswod",
        confirmPassword: "Kɔnfirm paswod",
        companyName: "Kɔmpin nem",
        contactName: "Fɔl nem fɔ kontak pesin",
        workEmail: "Wok i-mel adres",
        firstName: "Fɔs nem",
        lastName: "Las nem",
        passwordHelp: "Yu paswod fɔ get 10 lɛta ɔ mɔ. Nɔ yus paswod we pipul kin gɛs izi.",
        termsPrefix: "A andastan an gri wit di",
        termsOfService: "Rul fɔ Yus",
        termsMiddle: ", Akɔnt Agriment, an di",
        privacyPolicy: "Prayvasi Polisi",
        termsSuffix: ".",
        alreadyHaveAccount: "Yu get akawnt finis?",
        signIn: "Lɔgin",
        googleSignup: "Sayn op wetin Google",
        facebookSignup: "Sayn op wetin Facebook",
      },
      login: {
        title: "Welkɔm Bak",
        subtitle: "Abeg lɔgin na yu akawnt",
        rememberMe: "Memba mi",
        forgotPassword: "Yu foget paswod?",
        submit: "LƆGIN",
        divider: "Ɔ",
        noAccount: "Yu nɔ get akawnt yet?",
        signUp: "Regista",
        google: "Kɔntinyu wetin Google",
        facebook: "Kɔntinyu wetin Facebook",
      },
      register: {
        studentTitle: "Mek yu akawnt",
        companyTitle: "Regista yu kɔmpin",
        studentSubtitle: "Yu nex chans de bigin ya.",
        companySubtitle: "Konek yu wok chans wit student dɛn.",
        student: "Student",
        company: "Kɔmpin",
        studentSubmit: "Mek student akawnt",
        companySubmit: "Mek kɔmpin akawnt",
        divider: "Ɔ sayn op wit",
      },
      accessibility: {
        logo: "EduNextSL logo",
        logoAlt: "EduNextSL Learning Solutions",
        slideIndicators: "Indiketa fɔ slide dɛn",
        viewSlide: "Luk {{title}}",
      },
      promo: {
        pastQuestions: {
          tag: "PLENTI OL EXAM KWƐSƆN DƐN",
          title: "Plenti Ol Exam Kwɛsɔn Dɛn",
          description:
            "Get ol nashɔn exam an buk fɔ praktis, fɔ yu sabi gud an pas yu exam dɛn.",
          alt: "Pikchɔ fɔ student dɛn we de stɔdi ol exam kwɛsɔn dɛn",
        },
        internships: {
          tag: "WOK PRAKTIS",
          title: "Wok Praktis fɔ Yu Nex Step",
          description:
            "Fɛn wok chans, lan gud skil, an mit wok pesin dɛn we kin help yu fɔ go fɔwod.",
          alt: "Pikchɔ fɔ wan wok praktis chans",
        },
        scholarships: {
          tag: "SKOLARSHIP",
          title: "Skolarship fɔ Yu Nex Step",
          description:
            "Fɛn moni fɔ skul an help we kin mek student dɛn du gud an fɔkus na dem stɔdi.",
          alt: "Pikchɔ fɔ wan skolarship chans",
        },
      },
    },
  },
  fr: {
    translation: {
      language: { label: "Langue" },
      common: {
        email: "E-mail",
        emailAddress: "Adresse e-mail",
        password: "Mot de passe",
        confirmPassword: "Confirmer le mot de passe",
        companyName: "Nom de l’entreprise",
        contactName: "Nom complet du contact",
        workEmail: "Adresse e-mail professionnelle",
        firstName: "Prénom",
        lastName: "Nom",
        passwordHelp: "Utilisez au moins 10 caractères. Évitez les mots de passe courants ou uniquement numériques.",
        termsPrefix: "Je comprends et j’accepte les",
        termsOfService: "Conditions d’utilisation",
        termsMiddle: ", l’accord utilisateur et la",
        privacyPolicy: "Politique de confidentialité",
        termsSuffix: ".",
        alreadyHaveAccount: "Vous avez déjà un compte ?",
        signIn: "Se connecter",
        googleSignup: "S’inscrire avec Google",
        facebookSignup: "S’inscrire avec Facebook",
      },
      login: {
        title: "Bon retour",
        subtitle: "Connectez-vous à votre compte",
        rememberMe: "Se souvenir de moi",
        forgotPassword: "Mot de passe oublié ?",
        submit: "CONNEXION",
        divider: "Ou",
        noAccount: "Vous n’avez pas de compte ?",
        signUp: "S’inscrire",
        google: "Continuer avec Google",
        facebook: "Continuer avec Facebook",
      },
      register: {
        studentTitle: "Créez votre compte",
        companyTitle: "Inscrire votre entreprise",
        studentSubtitle: "Votre prochaine opportunité commence ici.",
        companySubtitle: "Reliez vos opportunités aux talents étudiants.",
        student: "Étudiant",
        company: "Entreprise",
        studentSubmit: "Créer un compte étudiant",
        companySubmit: "Créer un compte entreprise",
        divider: "Ou s’inscrire avec",
      },
      accessibility: {
        logo: "Logo EduNextSL",
        logoAlt: "EduNextSL Solutions d’apprentissage",
        slideIndicators: "Indicateurs du carrousel",
        viewSlide: "Voir {{title}}",
      },
      promo: {
        pastQuestions: {
          tag: "ANNALES D’EXAMENS",
          title: "Annales et sujets d’examen",
          description:
            "Accédez à des annales vérifiées et à des guides pour mieux vous entraîner, suivre vos progrès et réussir vos examens.",
          alt: "Illustration d’étudiants révisant avec des annales",
        },
        internships: {
          tag: "STAGES",
          title: "Des stages pour avancer",
          description:
            "Découvrez des expériences pratiques, développez vos compétences et trouvez des employeurs qui feront avancer votre carrière.",
          alt: "Illustration d’une opportunité de stage",
        },
        scholarships: {
          tag: "BOURSES",
          title: "Des bourses pour la suite",
          description:
            "Découvrez des aides financières et des programmes conçus pour accompagner la réussite des étudiants.",
          alt: "Illustration d’une opportunité de bourse",
        },
      },
    },
  },
};

const savedLanguage = window.localStorage.getItem("edunextsl-language") ?? "en";

void i18n.use(initReactI18next).init({
  resources,
  lng: savedLanguage,
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

document.documentElement.lang = i18n.resolvedLanguage ?? savedLanguage;

i18n.on("languageChanged", (language) => {
  document.documentElement.lang = language;
});

export default i18n;
