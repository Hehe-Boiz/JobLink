import React, { useState } from 'react';
import { View, Image, TouchableOpacity, Animated } from 'react-native';
import CustomText from '../common/CustomText'; 
import styles from '../../styles/Candidate/CompanyListStyles';
const NO_RESULT_IMG = require('../../../assets/images/Illustrasi.png');

const CompanyCard = ({ item }) => {
    const [isFollowing, setIsFollowing] = useState(false);

    const handlePress = () => {
        setIsFollowing(!isFollowing);
    };

    return (
        <View style={styles.cardContainer}>
            {/* Logo Section */}
            <View style={[styles.logoContainer, { backgroundColor: item.bg || '#FFF' }]}>
                <Image
                    source={{uri: item.logo}}
                    style={styles.logo}
                    resizeMode="contain"
                />
            </View>

            {/* Info Section */}
            <CustomText style={styles.companyName}>{item.name}</CustomText>
            <CustomText style={styles.followers}>{item.followers} Followers</CustomText>

            {/* Button Section */}
            <TouchableOpacity
                style={[styles.followBtn, isFollowing && styles.followBtnActive]}
                onPress={handlePress}
                activeOpacity={0.7}
            >
                <CustomText style={[styles.btnText, isFollowing && styles.btnTextActive]}>
                    {isFollowing ? 'Followed' : 'Follow'}
                </CustomText>
            </TouchableOpacity>
        </View>
    );
};

export default CompanyCard;