import React from "react";
import {Image, TouchableOpacity, View, Text, StyleSheet} from "react-native";
import {MaterialCommunityIcons} from "@expo/vector-icons";

const NotificationCard = ({item, onPress, onMore, onDelete}) => {
    const isApplication = item.type === "application";

    return (
        <TouchableOpacity
            activeOpacity={0.9}
            onPress={onPress}
            style={[styles.card, item.unread ? styles.cardUnread : styles.cardRead]}
        >
            <View style={styles.cardTop}>
                <View style={styles.row}>
                    <View style={styles.logoWrap}>
                        <Image source={{uri: item.logo}} style={styles.logo}/>
                    </View>

                    <View style={{flex: 1}}>
                        <Text style={styles.cardTitle}>{item.title}</Text>
                        <Text style={styles.cardMsg} numberOfLines={2}>
                            {item.message}
                        </Text>
                    </View>

                    <TouchableOpacity onPress={onMore} style={styles.moreBtn}>
                        <MaterialCommunityIcons name="dots-vertical" size={18} color="#6B6B6B"/>
                    </TouchableOpacity>
                </View>
            </View>

            <View style={styles.cardBottom}>
                {item.ctaText ? (
                    <TouchableOpacity style={styles.ctaBtn} onPress={onPress}>
                        <Text style={styles.ctaText}>{item.ctaText}</Text>
                    </TouchableOpacity>
                ) : (
                    <View/>
                )}

                <View style={styles.bottomRight}>
                    <Text style={styles.timeText}>{item.time}</Text>

                    {isApplication ? (
                        <TouchableOpacity onPress={onDelete} style={styles.inlineDelete}>
                            <Text style={styles.deleteText}>Delete</Text>
                        </TouchableOpacity>
                    ) : null}
                </View>
            </View>
        </TouchableOpacity>
    );
};

export default NotificationCard;

const styles = StyleSheet.create({
    card: {
        borderRadius: 18,
        padding: 14,
        marginBottom: 12,
        borderWidth: 1,
        borderColor: "#EEF0F6",
    },
    cardUnread: {
        backgroundColor: "rgba(117,81,255,0.2)"
    },
    cardRead: {
        backgroundColor: "#FFFFFF"
    },

    cardTop: {
        marginBottom: 10
    },

    row: {
        flexDirection: "row",
        alignItems: "flex-start",

        gap: 10,
    },

    logoWrap: {
        width: 42,
        height: 42,
        borderRadius: 12,
        backgroundColor: "#FFFFFF",
        alignItems: "center",
        justifyContent: "center",
        overflow: "hidden",
    },
    logo: {
        width: 28,
        height: 28,
        resizeMode: "contain"
    },

    moreBtn: {
        width: 34,
        height: 34,
        alignItems: "center",
        justifyContent: "center"
    },

    cardTitle: {
        fontSize: 14,
        fontWeight: "700",
        color: "#1D1D1D"
    },
    cardMsg: {
        marginTop: 4,
        fontSize: 12,
        color: "#6A6A6A",
        lineHeight: 16
    },

    cardBottom: {
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-between"
    },

    ctaBtn: {
        paddingHorizontal: 16,
        paddingVertical: 9,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: "#D9DDEB",
        backgroundColor: "#FFFFFF",
    },
    ctaText: {
        fontSize: 12,
        fontWeight: "700",
        color: "#2B2B2B"
    },

    bottomRight: {
        alignItems: "flex-end",
        gap: 6
    },
    timeText: {
        fontSize: 11,
        color: "#8A8A8A"
    },

    inlineDelete: {
        paddingHorizontal: 4,
        paddingVertical: 2
    },
    deleteText: {
        fontSize: 11,
        color: "#FF3B30",
        fontWeight: "700"
    },
});
