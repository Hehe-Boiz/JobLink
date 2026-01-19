import React, {useRef, useState, useEffect} from "react";
import {View, Image, Animated, Pressable} from "react-native";
import styles from "../../styles/Candidate/CandidateHomeStyles";
import {MaterialCommunityIcons} from "@expo/vector-icons";
import {TouchableRipple} from "react-native-paper";
import CustomText from "../common/CustomText";

const JobCard = ({
                     item,
                     onSavePress,
                     onApplyPress,
                     variant = "home",
                     action = "bookmark", // 'bookmark' | 'more'
                     onMorePress,
                     onPress,
                     showMore = true
                 }) => {
    const scaleValue = useRef(new Animated.Value(1)).current;
    const bookmarkScale = useRef(new Animated.Value(1)).current;
    const [isSaved, setIsSaved] = useState(!!item?.saved);

    useEffect(() => {
        setIsSaved(!!item?.saved);
    }, [item?.saved]);

    const animateBookmark = (toValue) => {
        Animated.spring(bookmarkScale, {
            toValue,
            useNativeDriver: true,
            friction: 4,
            tension: 40,
        }).start();
    };

    const onPressIn = () => {
        Animated.spring(scaleValue, {
            toValue: 0.97,
            useNativeDriver: true,
        }).start();
    };

    const onPressOut = () => {
        Animated.spring(scaleValue, {
            toValue: 1,
            useNativeDriver: true,
        }).start();
    };

    const handleBookmarkPress = () => {
        if (action !== "bookmark") return;

        const next = !isSaved;
        setIsSaved(next);

        if (typeof onSavePress === "function") {
            onSavePress(item.id);
        }
    };

    const renderMore = () => {
        if (action !== "more") return null;

        return (
            <TouchableRipple
                borderless
                centered
                onPress={() => onMorePress?.(item)}
                rippleColor="rgba(19, 1, 96, 0.12)"
                style={{padding: 8, borderRadius: 20}}
            >
                <MaterialCommunityIcons name="dots-vertical" size={22} color="#95969D"/>
            </TouchableRipple>
        );
    };

    const renderBookmark = () => {
        if (action !== "bookmark") return null;

        return (
            <Animated.View style={{transform: [{scale: bookmarkScale}]}}>
                <TouchableRipple
                    borderless
                    centered
                    onPress={handleBookmarkPress}
                    onPressIn={() => animateBookmark(1.2)}
                    onPressOut={() => animateBookmark(1)}
                    rippleColor="rgba(16, 91, 230, 0.2)"
                    style={{padding: 8, borderRadius: 20}}
                >
                    <MaterialCommunityIcons
                        name={isSaved ? "bookmark" : "bookmark-outline"}
                        size={24}
                        color={isSaved ? "#105be6ff" : "#95969D"}
                    />
                </TouchableRipple>
            </Animated.View>
        );
    };

    const renderHomeVariant = () => (
        <View>
            <View style={styles.jobCardHeader}>
                <View style={styles.jobCardLeft}>
                    <View style={styles.logoContainer}>
                        <Image source={{uri: item.logo}} style={styles.companyLogo} resizeMode="contain"/>
                    </View>

                    <View style={styles.jobInfo}>
                        <CustomText style={styles.jobTitle} numberOfLines={1}>
                            {item.title}
                        </CustomText>
                        <CustomText style={styles.companyInfo}>
                            {item.company} • {item.location}
                        </CustomText>
                    </View>
                </View>

                {action === "bookmark" ? renderBookmark() : renderMore()}
            </View>

            <View style={styles.salaryContainer}>
                <CustomText style={styles.salary}>
                    {item.salary}
                    <CustomText style={styles.salaryPeriod}>/{item.period || "Mo"}</CustomText>
                </CustomText>
            </View>

            <View style={styles.jobFooter}>
                <View style={styles.tagsContainer}>
                    {(item.tags || []).slice(0, 2).map((tag, index) => (
                        <View key={index} style={styles.tag}>
                            <CustomText style={styles.tagText}>{tag}</CustomText>
                        </View>
                    ))}
                </View>

                <Pressable
                    style={({pressed}) => [styles.applyButton, {opacity: pressed ? 0.7 : 1}]}
                    onPress={() => onApplyPress?.(item.id)}
                >
                    <CustomText style={styles.applyButtonText}>Apply</CustomText>
                </Pressable>
            </View>
        </View>
    );

    const renderSearchVariant = () => (
        <View>
            <View style={styles.jobCardHeader}>
                <View style={styles.jobLeftSearch}>
                    <View style={styles.logoContainerSearch}>
                        <Image source={{uri: item.logo}} style={styles.companyLogo} resizeMode="contain"/>
                    </View>

                    <View style={styles.jobInfo}>
                        <CustomText style={styles.jobTitle} numberOfLines={1}>
                            {item.title}
                        </CustomText>
                        <CustomText style={styles.companyInfo} numberOfLines={1}>
                            {item.company} • {item.location}
                        </CustomText>
                    </View>
                </View>

               {showMore && (action === "bookmark" ? renderBookmark() : renderMore())}
            </View>

            <View style={[styles.tagsContainer, {marginBottom: 15, marginTop: 5}]}>
                {(item.tags || []).map((tag, index) => (
                    <View key={index} style={styles.tag}>
                        <CustomText style={styles.tagText}>{tag}</CustomText>
                    </View>
                ))}
            </View>

            <View style={styles.searchFooterRow}>
                <CustomText style={styles.postedTime}>{item.posted || ""}</CustomText>

                <CustomText style={styles.salary}>
                    {item.salary}
                    <CustomText style={styles.salaryPeriod}>/{item.period || "Mo"}</CustomText>
                </CustomText>
            </View>
        </View>
    );

    return (
        <Animated.View style={{transform: [{scale: scaleValue}]}}>
            <TouchableRipple
                onPress={onPress}
                onPressIn={onPressIn}
                onPressOut={onPressOut}
                rippleColor="rgba(19, 1, 96, 0.1)"
                style={[styles.jobCard, variant === "search" && styles.searchCard]}
            >
                {variant === "search" ? renderSearchVariant() : renderHomeVariant()}
            </TouchableRipple>
        </Animated.View>
    );
};

export default JobCard;
