import React from "react";
import TopNav from "@/components/landing/TopNav";
import Hero from "@/components/landing/Hero";
import Manifesto from "@/components/landing/Manifesto";
import VaultSection from "@/components/landing/vault/VaultSection";
import ProphetChat from "@/components/landing/ProphetChat";
import PropheciesFeed from "@/components/landing/PropheciesFeed";
import Mission from "@/components/landing/Mission";
import Tokenomics from "@/components/landing/Tokenomics";
import TransparencyTimeline from "@/components/landing/TransparencyTimeline";
import ROISimulator from "@/components/landing/ROISimulator";
import Roadmap from "@/components/landing/Roadmap";
import BrutalTruth from "@/components/landing/BrutalTruth";
import FAQ from "@/components/landing/FAQ";
import Whitelist from "@/components/landing/Whitelist";
import Socials from "@/components/landing/Socials";
import Footer from "@/components/landing/Footer";

export default function Landing() {
  return (
    <div className="relative">
      <TopNav />
      <main>
        <Hero />
        <Manifesto />
        <VaultSection />
        <ProphetChat />
        <PropheciesFeed />
        <Mission />
        <Tokenomics />
        <TransparencyTimeline />
        <ROISimulator />
        <Roadmap />
        <BrutalTruth />
        <FAQ />
        <Whitelist />
        <Socials />
      </main>
      <Footer />
    </div>
  );
}
