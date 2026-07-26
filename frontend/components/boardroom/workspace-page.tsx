import { BoardroomApp } from "@/components/boardroom/boardroom-app";
import { AuthGate } from "@/components/boardroom/auth-gate";

export function WorkspacePage() {
  return (
    <AuthGate>
      <BoardroomApp />
    </AuthGate>
  );
}
