import React from 'react';
import {Text, StyleSheet} from 'react-native';
const CustomText = ({style, children, ...props}) => {
    const flattenedStyle = Array.isArray(style)
        ? Object.assign({}, ...style)
        : style || {};

    const fontWeight = flattenedStyle.fontWeight || '400';

    const fontFamilyMap = {
        '100': 'DMSans-Thin',
        '200': 'DMSans-ExtraLight',
        '300': 'DMSans-Light',
        '400': 'DMSans-Regular',
        'normal': 'DMSans-Regular',
        '500': 'DMSans-Medium',
        '600': 'DMSans-SemiBold',
        '700': 'DMSans-Bold',
        'bold': 'DMSans-Bold',
        '800': 'DMSans-ExtraBold',
        '900': 'DMSans-Black',
    };

    const fontFamily = fontFamilyMap[fontWeight] || 'DMSans-Regular';

    const fontStyle = flattenedStyle.fontStyle;
    let finalFontFamily = fontFamily;

    if (fontStyle === 'italic') {
        const italicMap = {
            'DMSans-Thin': 'DMSans-ThinItalic',
            'DMSans-ExtraLight': 'DMSans-ExtraLightItalic',
            'DMSans-Light': 'DMSans-LightItalic',
            'DMSans-Regular': 'DMSans-Italic',
            'DMSans-Medium': 'DMSans-MediumItalic',
            'DMSans-SemiBold': 'DMSans-SemiBoldItalic',
            'DMSans-Bold': 'DMSans-BoldItalic',
            'DMSans-ExtraBold': 'DMSans-ExtraBoldItalic',
            'DMSans-Black': 'DMSans-BlackItalic',
        };
        finalFontFamily = italicMap[fontFamily] || fontFamily;
    }

    return (
        <Text
            style={[
                styles.default,
                {fontFamily: finalFontFamily},
                style,
                {
                    fontWeight: undefined,
                    fontStyle: undefined,
                }
            ]}
            {...props}
        >
            {children}
        </Text>
    );
};

const styles = StyleSheet.create({
    default: {
        fontFamily: 'DMSans-Regular',
        includeFontPadding: false,
    },
});

export default CustomText;