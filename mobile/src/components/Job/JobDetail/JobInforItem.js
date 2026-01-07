import React from 'react';
import { View } from 'react-native';
import CustomText from '../../CustomText';
import styles from '../../../styles/Job/JobDetailStyles';

const JobInforItem = ({ title, value, isLast }) => {
    return (
        <View style={styles.infoItemContainer}>
            <CustomText style={styles.infoItemTitle}>{title}</CustomText>

            <CustomText style={styles.infoItemValue}>{value}</CustomText>

            <View style={styles.infoItemSeparator} />
        </View>
    );
};

export default JobInforItem;