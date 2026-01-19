import React, {useMemo, useRef, useState} from "react";
import {
    View,
    StyleSheet,
    FlatList,
    TouchableOpacity,
    Modal,
    Pressable,
    Animated,
    Dimensions,
    StatusBar,
    Text,
    PanResponder
} from "react-native";
import {SafeAreaView} from "react-native-safe-area-context";
import {MaterialCommunityIcons} from "@expo/vector-icons";

const {height: screenHeight} = Dimensions.get("window");
import NotificationCard from "../../../components/Candidate/NotificationCard";

const CLOSE_THRESHOLD = 120;

// Mock icons (dùng url logo như các screen trước của bạn)
const MOCK_NOTIFICATIONS = [
    {
        id: "1",
        type: "application",
        title: "Application sent",
        message: "Applications for Google inc have entered for company review",
        time: "25 minutes ago",
        logo: "https://img.icons8.com/color/480/google-logo.png",
        unread: true,
    },
    {
        id: "2",
        type: "application",
        title: "Application sent",
        message: "Applications for Dribbble companies have entered for company review",
        time: "45 minutes ago",
        logo: "https://img.icons8.com/fluency/480/dribbble.png",
        unread: false,
    },
    {
        id: "3",
        type: "job",
        title: "Your job notification",
        message: "Brandon, there are 10+ new jobs for UI/UX Designer in California, USA",
        time: "1 hour",
        logo: "https://img.icons8.com/color/480/figma--v1.png",
        unread: true,
        ctaText: "See new job",
    },
    {
        id: "4",
        type: "job",
        title: "Twitter inc is looking for a UI/UX Designer.",
        message: "Check out this and 9 other job recommendations",
        time: "6 hours",
        logo: "https://img.icons8.com/color/480/twitter--v1.png",
        unread: false,
        ctaText: "See job",
    },
    {
        id: "5",
        type: "application",
        title: "Application sent",
        message: "Applications for Apple companies have entered for company review",
        time: "1 day ago",
        logo: "https://img.icons8.com/ios-filled/500/mac-os.png",
        unread: false,
    },
];


const EmptyNotifications = () => {
    return (
        <View style={styles.emptyWrap}>
            <View style={styles.emptyIcon}>
                <MaterialCommunityIcons name="bell-outline" size={54} color="#2F39E4"/>
            </View>
            <Text style={styles.emptyTitle}>No notifications</Text>
            <Text style={styles.emptySub}>You have no notifications at this time{"\n"}thank you</Text>
        </View>
    );
};

const NotificationsScreen = ({navigation}) => {
    const [items, setItems] = useState(MOCK_NOTIFICATIONS);

    // Bottom sheet state
    const [sheetVisible, setSheetVisible] = useState(false);
    const [selectedItem, setSelectedItem] = useState(null);

    const translateY = useRef(new Animated.Value(screenHeight)).current;

    const openSheet = (item) => {
        setSelectedItem(item);
        setSheetVisible(true);
        translateY.setValue(screenHeight);

        Animated.spring(translateY, {
            toValue: 0,
            useNativeDriver: true,
            friction: 8,
            tension: 60,
        }).start();
    };

    const closeSheet = () => {
        Animated.timing(translateY, {
            toValue: screenHeight,
            duration: 180,
            useNativeDriver: true,
        }).start(() => {
            setSheetVisible(false);
            setSelectedItem(null);
        });
    };

    const panResponder = useMemo(
        () =>
            Animated.createAnimatedComponent
                ? null
                : null,
        []
    );

    const sheetPanResponder = useMemo(() => {
        let startY = 0;

        return PanResponder.create({
            onStartShouldSetPanResponder: () => true,
            onMoveShouldSetPanResponder: () => true,

            onPanResponderGrant: () => {
                translateY.stopAnimation((v) => {
                    startY = v; // v đang là translateY hiện tại
                });
            },

            onPanResponderMove: (_, gestureState) => {
                // gestureState.dy luôn tồn tại trong PanResponder
                const next = Math.max(0, startY + gestureState.dy);
                translateY.setValue(next);
            },

            onPanResponderRelease: (_, gestureState) => {
                if (gestureState.dy > CLOSE_THRESHOLD) {
                    closeSheet();
                } else {
                    Animated.spring(translateY, {
                        toValue: 0,
                        useNativeDriver: true,
                        friction: 8,
                        tension: 60,
                    }).start();
                }
            },
        });
    }, [translateY]);

    const markReadAll = () => {
        setItems((prev) => prev.map((x) => ({...x, unread: false})));
    };

    const deleteOne = (id) => {
        setItems((prev) => prev.filter((x) => x.id !== id));
    };

    const deleteSelectedFromSheet = () => {
        if (!selectedItem) return;
        deleteOne(selectedItem.id);
        closeSheet();
    };

    const goDetail = (item) => {
        // Bạn có thể tách: application -> detail screen, job -> job detail screen
        navigation?.navigate?.("NotificationDetail", {item});
    };

    const renderItem = ({item}) => (
        <NotificationCard
            item={item}
            onPress={() => goDetail(item)}
            onMore={() => openSheet(item)}
            onDelete={() => deleteOne(item.id)}
        />
    );

    const isEmpty = items.length === 0;

    return (
        <SafeAreaView style={styles.safe} edges={["top"]}>
            <StatusBar barStyle="dark-content"/>
            <View style={styles.header}>
                <TouchableOpacity onPress={() => navigation?.goBack?.()} style={styles.backBtn}>
                    <MaterialCommunityIcons name="chevron-left" size={26} color="#0B0B0B"/>
                </TouchableOpacity>

                <Text style={styles.headerTitle}>Notifications</Text>

                <TouchableOpacity onPress={markReadAll} style={styles.readAllBtn}>
                    <Text style={styles.readAllText}>Read all</Text>
                </TouchableOpacity>
            </View>

            {isEmpty ? (
                <EmptyNotifications/>
            ) : (
                <FlatList
                    data={items}
                    keyExtractor={(x) => x.id}
                    renderItem={renderItem}
                    contentContainerStyle={styles.listContent}
                    showsVerticalScrollIndicator={false}
                />
            )}

            {/* Bottom Sheet */}
            <Modal visible={sheetVisible} transparent animationType="none" onRequestClose={closeSheet}>
                <Pressable style={styles.backdrop} onPress={closeSheet}/>

                <Animated.View
                    style={[
                        styles.sheet,
                        {
                            transform: [{translateY}],
                        },
                    ]}
                    {...sheetPanResponder.panHandlers}
                >
                    <View style={styles.sheetHandle}/>

                    <TouchableOpacity style={styles.sheetRow} onPress={deleteSelectedFromSheet}>
                        <MaterialCommunityIcons name="trash-can-outline" size={22} color="#1B1B1B"/>
                        <Text style={styles.sheetText}>Delete</Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={styles.sheetRow}
                        onPress={() => {
                            // demo: “Turn off notifications” cho 1 item
                            closeSheet();
                        }}
                    >
                        <MaterialCommunityIcons name="bell-off-outline" size={22} color="#1B1B1B"/>
                        <Text style={styles.sheetText}>Turn off notifications</Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={[styles.sheetRow, styles.sheetPrimaryRow]}
                        onPress={() => {
                            closeSheet();
                            navigation?.navigate?.("NotificationSettings");
                        }}
                    >
                        <MaterialCommunityIcons name="cog-outline" size={22} color="#FFFFFF"/>
                        <Text style={[styles.sheetText, {color: "#FFFFFF"}]}>Setting</Text>
                    </TouchableOpacity>
                </Animated.View>
            </Modal>
        </SafeAreaView>
    );
};

export default NotificationsScreen;

const styles = StyleSheet.create({
    safe: {
        flex: 1,
        backgroundColor: "#F9F9F9"
    },

    header: {
        height: 56,
        flexDirection: "row",
        alignItems: "center",
        paddingHorizontal: 14,
    },
    backBtn: {
        width: 40,
        height: 40,
        alignItems: "center",
        justifyContent: "center"
    },
    headerTitle: {
        flex: 1,
        textAlign: "center",
        fontSize: 18,
        fontWeight: "700",
        color: "#131313"
    },
    readAllBtn: {
        paddingHorizontal: 6,
        paddingVertical: 6
    },
    readAllText: {
        fontSize: 12,
        color: "#FF7A00",
        fontWeight: "600"
    },

    listContent: {
        paddingHorizontal: 14,
        paddingTop: 10,
        paddingBottom: 22
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
        justifyContent: "space-between",
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

    backdrop: {
        ...StyleSheet.absoluteFillObject,
        backgroundColor: "rgba(0,0,0,0.45)",
    },
    sheet: {
        position: "absolute",
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "#FFFFFF",
        borderTopLeftRadius: 22,
        borderTopRightRadius: 22,
        paddingTop: 10,
        paddingBottom: 22,
        paddingHorizontal: 18,
    },
    sheetHandle: {
        alignSelf: "center",
        width: 46,
        height: 4,
        borderRadius: 4,
        backgroundColor: "#D8D8D8",
        marginBottom: 12,
    },
    sheetRow: {
        flexDirection: "row",
        alignItems: "center",
        gap: 12,
        paddingVertical: 14,
    },
    sheetText: {
        fontSize: 14,
        fontWeight: "500",
        color: "#3B4657"
    },
    sheetPrimaryRow: {
        marginTop: 8,
        backgroundColor: "#130160130160",
        borderRadius: 14,
        paddingHorizontal: 14,
    },

    emptyWrap: {
        flex: 1,
        alignItems: "center",
        justifyContent: "center",
        paddingHorizontal: 24
    },
    emptyIcon: {
        width: 110,
        height: 110,
        borderRadius: 28,
        backgroundColor: "#F3F5FF",
        alignItems: "center",
        justifyContent: "center",
        marginBottom: 14,
    },
    emptyTitle: {
        fontSize: 18,
        fontWeight: "800",
        color: "#1B1B1B",
        marginBottom: 6
    },
    emptySub: {
        fontSize: 12,
        color: "#8B8B8B",
        textAlign: "center",
        lineHeight: 18
    },
});
