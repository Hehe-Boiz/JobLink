import {StyleSheet, Dimensions} from "react-native";

export default StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: "#F2F3F7",
    },
    headerContainer: {
        paddingHorizontal: 20,
        paddingBottom: 10,
        backgroundColor: "#F2F3F7",
    },
    headerTitle: {
        fontSize: 22,
        fontWeight: "700",
        color: "#1E1E1E",
        marginTop: 10,
    },
    subHeader: {
        fontSize: 14,
        color: "#6B6F76",
        marginBottom: 10,
    },

    legendScroll: {
        maxHeight: 60,
        marginBottom: 10,
    },
    legendContent: {
        paddingHorizontal: 16,
        alignItems: 'center',
    },
    legendItem: {
        flexDirection: "row",
        alignItems: "center",
        backgroundColor: "#FFF",
        paddingVertical: 6,
        paddingHorizontal: 10,
        borderRadius: 20,
        borderWidth: 1,
        marginRight: 10,
        minWidth: 120,
        maxWidth: 160,
    },
    legendLogo: {
        width: 24,
        height: 24,
        borderRadius: 12,
        marginRight: 8,
        backgroundColor: '#F0F0F0'
    },
    legendText: {
        fontSize: 12,
        fontWeight: "700",
        color: "#1E1E1E",
        flex: 1,
    },

    scrollContent: {
        paddingBottom: 40,
        paddingHorizontal: 16,
    },

    cardContainer: {
        backgroundColor: "#FFFFFF",
        borderRadius: 16,
        padding: 16,
        marginBottom: 16,
        shadowColor: "#95969D",
        shadowOffset: {width: 0, height: 4},
        shadowOpacity: 0.05,
        shadowRadius: 10,
        elevation: 2,
    },
    cardTitle: {
        fontSize: 14,
        color: "#AAA6B9",
        fontWeight: "600",
        textTransform: "uppercase",
        marginBottom: 12,
        letterSpacing: 0.5,
    },

    jobRow: {
        flexDirection: "row",
        alignItems: "flex-start",
        paddingVertical: 10,
        borderLeftWidth: 4,
        paddingLeft: 12,
        borderBottomWidth: 1,
        borderBottomColor: "#F5F5F5",
    },
    jobRowLast: {
        borderBottomWidth: 0,
    },
    jobRowContent: {
        flex: 1,
    },
    jobValue: {
        fontSize: 15,
        color: "#1E1E1E",
        fontWeight: "500",
        lineHeight: 22,
    },
    companyNameSmall: {
        fontSize: 11,
        color: "#9CA3AF",
        marginTop: 2,
        fontWeight: '500'
    },

    footerActions: {
        padding: 16,
        backgroundColor: "#FFF",
        borderTopWidth: 1,
        borderTopColor: "#EAEAEA",
    },
    applyBtn: {
        paddingVertical: 12,
        borderRadius: 8,
        alignItems: "center",
        justifyContent: "center",
        marginBottom: 8,
        flexDirection: 'row'
    },
    applyText: {
        color: "#FFFFFF",
        fontWeight: "700",
        fontSize: 14,
        marginLeft: 8
    },

});