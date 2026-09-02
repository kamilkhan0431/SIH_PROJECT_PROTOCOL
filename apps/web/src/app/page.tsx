import Link from "next/link";

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div>
          <h1>See the slope before it moves.</h1>
          <p>
            SlopeSense NER fuses rainfall, terrain, historical slides, and field photos into a four-level risk map for the
            eight north-eastern states — built for district rooms and village WhatsApp groups alike.
          </p>
          <p>
            <Link className="btn" href="/map">
              Open live GIS
            </Link>
          </p>
        </div>
        <div className="panel">
          <h2>Demo logins</h2>
          <p className="note">Password for all accounts: demo123</p>
          <div className="roles">
            <Link href="/login">citizen — community reporter</Link>
            <Link href="/login">field — ground official</Link>
            <Link href="/login">district — DEOC / East Khasi Hills story</Link>
            <Link href="/login">sdma — state / national watch desk</Link>
          </div>
        </div>
      </section>
      <section className="grid4">
        <div className="stat">
          <b>4</b>severity classes
        </div>
        <div className="stat">
          <b>8</b>NER states on one map
        </div>
        <div className="stat">
          <b>Offline</b>queue + PWA shell
        </div>
        <div className="stat">
          <b>EN HI AS BN</b>alert copy
        </div>
      </section>
    </>
  );
}
