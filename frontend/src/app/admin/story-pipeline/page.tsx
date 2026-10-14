"use client";

import { useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { StoryPipelineView } from "@/components/admin/StoryPipelineView";
import { Language } from "@/lib/i18n";
import { storage } from "@/lib/storage";
import { useRouter } from "next/navigation";

export default function StoryPipelinePage() {
  const router = useRouter();
  const [lang, setLang] = useState<Language>("vi");
  const user = storage.getUser();

  const handleTabChange = (tab: string) => {
    if (tab === "setup" || tab === "editor" || tab === "comic" || tab === "posts") {
      router.push(`/?tab=${tab}`);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-black text-white">
      <Sidebar
        username={user?.username || ""}
        fullName={user?.full_name || ""}
        lang={lang}
        onLanguageChange={setLang}
        onNewStory={() => router.push("/?tab=setup")}
        onOpenHistory={() => {}}
        onLogout={() => {
          storage.clear();
          router.push("/");
        }}
        activeTab="pipeline"
        onTabChange={handleTabChange}
      />
      <main className="flex-1 overflow-y-auto">
        <StoryPipelineView lang={lang} />
      </main>
    </div>
  );
}
