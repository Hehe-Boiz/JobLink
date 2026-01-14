import React from 'react';
import {View, StyleSheet, Linking} from 'react-native';
import CustomText from '../../common/CustomText';
import styles from "../../../styles/Job/JobDetailStyles";
import {useParsedList} from "../../../hooks/useParsedList";
import CompanyGallery from './CompanyGallery';

const JobDetailCompany = ({item}) => {
    const parserAbout = useParsedList(item?.about || "");

    const handleOpenWebsite = () => {
        if (item?.website) {
            Linking.openURL(item.website).catch(err =>
                console.error("Couldn't load page", err)
            );
        }
    };

    if (!item) return null;

    return (
        <View style={styles.containerJob}>
            <CustomText style={styles.contentTitle}>About Company</CustomText>
            {parserAbout.length > 0 ? (
                parserAbout.map((content, index) => (
                    <CustomText key={index} style={[styles.contentReq, styles.textAbout]}>
                        {content}
                    </CustomText>
                ))
            ) : (
                <CustomText style={[styles.contentReq, styles.textAbout]}>
                    Chưa có mô tả.
                </CustomText>
            )}
            <CustomText style={[styles.contentTitle, styles.mt_10, styles.mb_10]}>Website</CustomText>
            <CustomText
                style={styles.linkWeb}
                onPress={() => Linking.openURL('https://www.google.com')}
            >
                {item.website || "Đang cập nhật"}
            </CustomText>
            {item.info && item.info.map((itemInfo, index) => (
                <View key={index}>
                    <CustomText style={[styles.contentTitle, styles.mt_10, styles.mb_10]}>
                        {itemInfo.title}
                    </CustomText>
                    <CustomText style={styles.infoItemValue}>
                        {itemInfo.value}
                    </CustomText>
                </View>
            ))}
            {/*<CustomText style={[styles.contentTitle, styles.mt_20, styles.mb_20]}>Company Gallery</CustomText>*/}
            <CompanyGallery images={item.gallery}/>
        </View>
    );
};

export default JobDetailCompany;