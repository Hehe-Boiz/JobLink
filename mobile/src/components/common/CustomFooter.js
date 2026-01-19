import React from 'react';
import { View, TouchableOpacity, StyleSheet } from 'react-native';
import CustomText from './CustomText';
import styles from '../../styles/Job/JobDetailStyles';

const CustomFooter = ({
    onApply,
    applyTitle = "APPLY NOW",
    leftContent = null
}) => {
    return (
        <View style={localStyles.footerContainer}>
            {leftContent && (
                <View style={localStyles.leftWrapper}>
                    {leftContent}
                </View>
            )}

            <TouchableOpacity style={styles.btnApply} onPress={onApply}>
                <CustomText style={styles.btnApplyText}>{applyTitle}</CustomText>
            </TouchableOpacity>
        </View>
    );
};

const localStyles = StyleSheet.create({
    footerContainer: {
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        backgroundColor: '#FFFFFF',
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 20,
        paddingTop: 20,
        paddingBottom: 30,
        borderTopLeftRadius: 30,
        borderTopRightRadius: 30,
        elevation: 20,
        zIndex: 100,
    },
    leftWrapper: {
        marginRight: 15,
    }
});

export default CustomFooter;