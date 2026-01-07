import { StyleSheet } from "react-native";

export default StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F9F9F9',
    },
    headerTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#130160',
    },
    scrollContainer: {
        paddingHorizontal: 20,
        paddingTop: 10,
        paddingBottom: 120,
    },
    sectionWrapper: {
        marginBottom: 25,
    },
    sectionTitle: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#130160',
        marginBottom: 15,
    },

    sliderContainer: {
        height: 70,
        justifyContent: 'center',
        marginTop: 10,
        marginHorizontal: 15,
        position: 'relative',
    },
    trackBg: {
        height: 4,
        backgroundColor: '#EAEAEA',
        borderRadius: 3,
        width: '100%',
        position: 'absolute',
        top: 25,
    },
    trackActive: {
        height: 4,
        backgroundColor: '#FF9228',
        borderRadius: 3,
        position: 'absolute',
        top: 25,
    },
    thumb: {
        width: 23,
        height: 23,
        borderRadius: 14,
        backgroundColor: '#FFFFFF',
        borderWidth: 2,
        borderColor: '#130160',
        position: 'absolute',
        top: 14,
        elevation: 4,
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.2,
        shadowRadius: 4,
        zIndex: 2,
    },
    priceLabel: {
        position: 'absolute',
        top: 48,
        alignItems: 'center',
        width: 50,
    },
    priceText: {
        fontSize: 12,
        fontWeight: 'bold',
        color: '#130160',
    },

    chipContainer: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 10,
    },
    chipBtn: {
        paddingHorizontal: 20,
        paddingVertical: 12,
        borderRadius: 12,
        backgroundColor: '#FFF4E5',
    },
    chipBtnSelected: {
        backgroundColor: '#FF9228',
    },
    chipText: {
        color: '#524B6B',
        fontSize: 13,
        fontWeight: '500',
    },
    chipTextSelected: {
        color: '#FFFFFF',
        fontWeight: 'bold',
    },
});