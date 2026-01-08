import React, {useState} from 'react';
import {View, Image, StyleSheet, TouchableOpacity, Linking, Alert} from 'react-native';
import CustomText from '../common/CustomText';
import styles from '../../styles/Job/JobDetailStyles'
import { MaterialCommunityIcons } from '@expo/vector-icons';

const JobLogo = ({item, style}) => {
    // State giả lập cho nút Follow
    const [isFollowed, setIsFollowed] = useState(false);

    const handleFollow = () => {
        setIsFollowed(!isFollowed);
        // Gọi API follow tại đây nếu cần
    };

    const handleVisitWebsite = () => {
        // Mở link Google nếu không có link thật (item.website)
        const url = item.website || 'https://www.google.com';
        Linking.openURL(url).catch(err =>
            Alert.alert("Lỗi", "Không thể mở trang web này")
        );
    };
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
            <View style={styles.actionButtonsRow}>
                {/* Button Follow */}
                <TouchableOpacity
                    style={styles.actionBtn}
                    onPress={handleFollow}
                    activeOpacity={0.7}
                >
                    <MaterialCommunityIcons
                        name={isFollowed ? "check" : "plus"}
                        size={20}
                        color="#FF4D4D"
                    />
                    <CustomText style={styles.actionBtnText}>
                        {isFollowed ? "Followed" : "Follow"}
                    </CustomText>
                </TouchableOpacity>

                <TouchableOpacity
                    style={styles.actionBtn}
                    onPress={handleVisitWebsite}
                    activeOpacity={0.7}
                >
                    <MaterialCommunityIcons
                        name="export-variant"
                        size={20}
                        color="#FF4D4D"
                    />
                    <CustomText style={styles.actionBtnText}>Visit website</CustomText>
                </TouchableOpacity>
            </View>
        </View>
    )
};

export default JobLogo;