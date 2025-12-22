"use client";

import { useI18nContext } from '../context/I18nContext';

export const useI18n = () => {
    const { t, locale, setLocale } = useI18nContext();
    return { t, locale, setLocale };
};
