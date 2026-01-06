import React from 'react';
import {View, StyleSheet, Linking} from 'react-native';
import CustomText from '../../CustomText';
import styles from "../../../styles/Candidate/CandidateJobDetailStyles";
import {useParsedList} from "../../../hooks/useParsedList";
import CompanyGallery from './CompanyGallery';

const JobDetailCompany = ({item}) => {
    const parserAbout = useParsedList(item.aboutCompany)

    return (
        <View style={styles.containerJob}>
            <CustomText style={styles.contentTitle}>About Company</CustomText>
            {parserAbout.map((content, index) => (
                <CustomText key={index} style={[styles.contentReq, styles.textAbout]}>{content}</CustomText>
            ))}
            <CustomText style={[styles.contentTitle, styles.mt_10, styles.mb_10]}>Website</CustomText>
            <CustomText
                style={styles.linkWeb}
                onPress={() => Linking.openURL('https://www.google.com')}
            >
                https://www.google.com
            </CustomText>
            {item.company_info.map((itemInfo, index) => (
                <View key={index}>
                    <CustomText style={[styles.contentTitle, styles.mt_10, styles.mb_10]}>{itemInfo.title}</CustomText>
                    <CustomText style={styles.infoItemValue}>
                        {itemInfo.value}
                    </CustomText>
                </View>
            ))}
            <CustomText style={[styles.contentTitle, styles.mt_20, styles.mb_20]}>Company Gallery</CustomText>
            <CompanyGallery images={item.company_gallery} />
        </View>
    );
};

export default JobDetailCompany;