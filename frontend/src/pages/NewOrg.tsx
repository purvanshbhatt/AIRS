import { CreateWorkspaceScreen } from '../components/onboarding/CreateWorkspaceScreen';

/** /new-org: add another workspace from inside the app. Same screen as /onboarding. */
export default function NewOrg() {
  return (
    <div className="py-6 sm:py-10">
      <CreateWorkspaceScreen isAdditional />
    </div>
  );
}
