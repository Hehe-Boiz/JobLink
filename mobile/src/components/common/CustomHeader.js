import styles from "../../styles/Job/JobDetailStyles";
import {TouchableOpacity, View} from "react-native";
import React from "react";
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from './CustomText';

const CustomHeader = ({navigation, title, iconColor = "#1A1D1F", showMenu = true}) => {

    return (
        <View style={styles.headerNav}>
            <TouchableOpacity onPress={() => navigation?.canGoBack() ? navigation.goBack() : null}>
                <MaterialCommunityIcons name="arrow-left" size={24} color={iconColor}/>
            </TouchableOpacity>
            {title ? <CustomText style={styles.headerTitle}>{title}</CustomText> : null}
            {showMenu ? (
                <TouchableOpacity>
                    <MaterialCommunityIcons name="dots-horizontal" size={24} color={iconColor}/>
                </TouchableOpacity>) : (<View style={{width: 24}}/>)}

        </View>
    );
};

export default CustomHeader
