import {StyleSheet, Dimensions} from "react-native";
const { width } = Dimensions.get('window');


export default StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F9F9F9',
    },
    content: {
        flex: 1,
        paddingHorizontal: 15,
    },
    searchContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        marginTop: 10,
        marginBottom: 30,
    },
    searchWrapper: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#FFFFFF',
        borderRadius: 12,
        height: 50,
        paddingHorizontal: 15,
        marginRight: 15,
        elevation: 2,
    },
    searchIcon: {
        marginRight: 10,
    },
    searchInput: {
        flex: 1,
        fontSize: 14,
        color: '#130160',
        fontFamily: 'DMSans-Regular',
    },
    filterBtn: {
        width: 50,
        height: 50,
        backgroundColor: '#FCA34D',
        borderRadius: 12,
        justifyContent: 'center',
        alignItems: 'center',
        elevation: 3,
    },

    screenTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#130160',
        marginBottom: 20,
    },

    listContainer: {
        paddingBottom: 20,
    },
    columnWrapper: {
        justifyContent: 'space-between',
        marginBottom: 20,
        padding: 5
    },
    card: {
        width: (width - 65) / 2,
        height: 175,
        borderRadius: 20,
        padding: 20,
        justifyContent: 'center',
        alignItems: 'center',
        elevation: 4,
    },
    iconCircle: {
        width: 70,
        height: 70,
        borderRadius: 35,
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 20,
    },
    cardTitle: {
        fontSize: 16,
        fontWeight: 'bold',
        marginBottom: 8,
        textAlign: 'center',
    },
    cardCount: {
        fontSize: 14,
        fontWeight: '400',
        textAlign: 'center',
    },
});