import React from 'react';
import {View, Image, StyleSheet, TouchableOpacity} from 'react-native';
import CustomText from '../CustomText';
import styles from '../../styles/Job/JobDetailStyles'

const JobLogo = ({item, style}) => {
    return (
        <View style={styles.contentLogoContainer}>
            <View style={styles.logoWrapper}>
                <Image source={{uri: item.logo}} style={styles.logo}/>
            </View>
            <CustomText style={styles.jobTitle}>{item.title}</CustomText>
            <View style={styles.infoRow}>
                <CustomText style={styles.infoText}>{item.company}</CustomText>
                <View style={styles.dot}></View>
                <CustomText style={styles.infoText}>{item.location}</CustomText>
                <View style={styles.dot}></View>
                <CustomText style={styles.infoText}>{item.postedTime}</CustomText>
            </View>
        </View>
    )
};

export default JobLogo;