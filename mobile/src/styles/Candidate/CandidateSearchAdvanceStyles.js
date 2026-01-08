import {StyleSheet} from "react-native";

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
        marginBottom: 15,
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
        height: 3,
        backgroundColor: '#EAEAEA',
        borderRadius: 3,
        width: '100%',
        position: 'absolute',
        top: 25,
    },
    trackActive: {
        height: 3,
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
        shadowOffset: {width: 0, height: 2},
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
        borderRadius: 9,
        backgroundColor: '#ececec',
    },
    chipBtnSelected: {
        backgroundColor: '#FCA34D',
    },
    chipText: {
        color: '#524B6B',
        fontSize: 13,
        fontWeight: '500',
    },
    chipTextSelected: {
        color: '#FFFFFF',
        fontWeight: '600',
    },
    accordionHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 10
    },
    radioGroup: {
        gap: 15,
        paddingLeft: 5
    },
    radioRow: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    radioText: {
        fontSize: 14,
        color: '#524B6B',
        marginLeft: 12,
    },
    radioTextSelected: {
        color: '#130160',
        fontWeight: '500'
    },
    separator: {
        height: 1.5,
        backgroundColor: '#EAEAEA',
        marginTop: 15,
        marginBottom: 5
    },
});