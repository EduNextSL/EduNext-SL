import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = { children: ReactNode };
type State = { failed: boolean };

/**
 * Last line of defence: a runtime error in any page shows a recovery screen
 * instead of unmounting the whole app into a blank page.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { failed: false };

  static getDerivedStateFromError(): State {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Diagnostics for developers only; nothing is shown to the user.
    console.error("UI error:", error, info.componentStack);
  }

  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <main className="status-screen" role="alert">
        <h1>Something went wrong while loading this page.</h1>
        <p>Your information is safe. Please try again.</p>
        <div className="status-actions">
          <button
            type="button"
            className="primary-button status-button"
            onClick={() => this.setState({ failed: false })}
          >
            Try Again
          </button>
          <button
            type="button"
            className="text-link"
            onClick={() => window.location.assign("/")}
          >
            Go to home
          </button>
        </div>
      </main>
    );
  }
}
