import '../styles/globals.css'
import type { AppProps } from 'next/app'
import React, { useEffect, useState } from 'react';
import Head from 'next/head';

function MyApp({ Component, pageProps }: AppProps) {

  return (
    <>
      <Head>
        <meta name="viewport" content="viewport-fit=cover" />
        <meta name="description" content="Mito is the fastest way to do Python data science. Edit your data in a spreadsheet, and generate Python code automatically."/>
      </Head>
      <Component {...pageProps} />
    </>
  )
}

export default MyApp