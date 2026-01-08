import React from 'react';
import { View, StyleSheet } from 'react-native';
import CustomText from '../../common/CustomText';
import styles from '../../../styles/Job/JobDetailStyles'

const ListDots = ({ content }) => {
    return (
        <View style={styles.row}>
            <View style={styles.bulletContainer}>
                <CustomText style={styles.bullet}>{'\u2022'}</CustomText>
            </View>
            <View style={styles.textContainer}>
                <CustomText style={styles.contentReq}>{content}</CustomText>
            </View>
        </View>
    );
};


export default ListDots;