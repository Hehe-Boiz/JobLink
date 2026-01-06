import React, {useState} from 'react';
import {View, StyleSheet, Image, TouchableOpacity, Linking} from 'react-native';
import CustomText from '../../CustomText';
import ListDots from './ListDots';
import JobInfoItem from './JobInforItem';
import styles from '../../../styles/Candidate/CandidateJobDetailStyles'
import { useParsedList, useFacilities } from '../../../hooks/useParsedList';
const MAP_BG = require('../../../../assets/images/Map.png');
const PIN_ICON = require('../../../../assets/images/Icon_Locations.png');
const GOOGLE_ICON = 'https://cdn-icons-png.flaticon.com/512/300/300221.png';

const JobDescriptionTab = ({item}) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [showButton, setShowButton] = useState(false);
    const parsedRequirements = useParsedList(item.requirements);
    const parsedFacilities = useFacilities(item.facilities)

    const handleOpenGoogleMaps = () => {
        Linking.openURL(item.link_gg_map);
    };

    return (
        <View style={styles.containerJob}>
            <CustomText style={styles.contentTitle}>Job Description</CustomText>
            <CustomText
                numberOfLines={isExpanded ? undefined : 3}
                ellipsizeMode="tail"
                onTextLayout={(e) => {
                    if (e.nativeEvent.lines.length > 3) setShowButton(true);
                }}
                style={styles.descText}
            >
                {item.desc}
            </CustomText>

            <View style={styles.btnContainerRead}>
                <TouchableOpacity
                    style={styles.btnRead}
                    onPress={() => setIsExpanded(!isExpanded)}
                >
                    <CustomText>{isExpanded ? "Read less" : "Read more"}</CustomText>
                </TouchableOpacity>
            </View>

            <CustomText style={styles.contentTitle}>Requirements</CustomText>
            {parsedRequirements.map((req, index) => (
                <ListDots key={index} content={req}/>
            ))}

            <CustomText style={styles.contentTitle}>Location</CustomText>
            <CustomText style={[styles.textContainer, styles.mb_10]}>
                {item.street}
            </CustomText>

            <View style={styles.mapContainer}>
                <Image source={MAP_BG} style={styles.mapImage} resizeMode="cover"/>
                <View style={styles.pinOverlay}>
                    <Image source={PIN_ICON} style={styles.pinImage} resizeMode="contain"/>
                </View>
            </View>

            <TouchableOpacity style={[styles.buttonGG, styles.mb_20]} onPress={handleOpenGoogleMaps}>
                <Image source={{uri: GOOGLE_ICON}} style={styles.buttonIconGG}/>
                <CustomText style={styles.buttonTextGG}>Open in Google Maps</CustomText>
            </TouchableOpacity>

            <CustomText style={styles.contentTitle}>Informations</CustomText>
            <View style={{marginTop: 20}}>
                {item.info.map((infoItem, index) => (
                    <JobInfoItem
                        key={index}
                        title={infoItem.title}
                        value={infoItem.value}
                        isLast={index === item.info.length - 1}
                    />
                ))}
            </View>

            <CustomText style={styles.contentTitle}>Facilities and Others</CustomText>
            {parsedFacilities.map((req, index) => (
                <ListDots key={index} content={req}/>
            ))}
        </View>
    );
};


export default JobDescriptionTab;