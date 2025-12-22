"use client";

import React, { createContext, useContext, useState, ReactNode } from 'react';
import en from '../locales/en.json';

type LocaleData = typeof en;

interface I18nContextType {
    t: (key: string) => string;
    locale: string;
    setLocale: (locale: string) => void;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

export const I18nProvider = ({ children }: { children: ReactNode }) => {
    const [locale, setLocale] = useState('en');
    const [translations] = useState<any>(en);

    const t = (key: string): string => {
        const keys = key.split('.');
        let result = translations;

        for (const k of keys) {
            if (result && result[k]) {
                result = result[k];
            } else {
                return key; // Fallback to key if not found
            }
        }

        return typeof result === 'string' ? result : key;
    };

    return (
        <I18nContext.Provider value={{ t, locale, setLocale }}>
            {children}
        </I18nContext.Provider>
    );
};

export const useI18nContext = () => {
    const context = useContext(I18nContext);
    if (!context) {
        throw new Error('useI18n must be used within an I18nProvider');
    }
    return context;
};
