import Head from 'next/head';
import '../styles/globals.css';

export default function App({ Component, pageProps }) {
  return (
    <>
      <Head>
        <title>TechMart Support Console</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta
          name="description"
          content="Multi-agent AI customer support assistant using RAG and LLMs."
        />
      </Head>
      <Component {...pageProps} />
    </>
  );
}
